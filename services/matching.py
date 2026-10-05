"""
Smart Matching Engine for SECONDLIFE.
Compares user's available components against project requirements
and calculates real feasibility scores.
"""

import json
from models.models import db, Component, Project, ProjectComponent, Match, UserComponent


def normalize_name(name):
    """Normalize a component name for comparison."""
    return name.lower().strip()


def names_match(user_comp_name, required_comp_name):
    """
    Check if a user's component name matches a required component name.
    Uses case-insensitive substring matching for flexibility.
    """
    u = normalize_name(user_comp_name)
    r = normalize_name(required_comp_name)
    # Exact match
    if u == r:
        return True
    # One contains the other
    if r in u or u in r:
        return True
    # Check individual words overlap (at least 2 significant words match)
    u_words = set(u.split())
    r_words = set(r.split())
    # Remove common small words
    stop_words = {'a', 'an', 'the', 'and', 'or', 'of', 'for', 'with', 'module', 'board'}
    u_significant = u_words - stop_words
    r_significant = r_words - stop_words
    if u_significant and r_significant:
        overlap = u_significant & r_significant
        if len(overlap) >= 1 and len(overlap) >= len(r_significant) * 0.5:
            return True
    return False


def find_matching_components(user_id, project_id):
    """
    Find matching components between a user's inventory and a project's requirements.

    Returns a dict with:
        - project_id
        - feasibility_score (0-100)
        - matched: list of matched component dicts
        - missing: list of missing component dicts
        - total_required: total units required
        - total_satisfied: total units the user can supply
    """
    project = Project.query.get(project_id)
    if not project:
        return None

    required_components = ProjectComponent.query.filter_by(project_id=project_id).all()
    if not required_components:
        return {
            'project_id': project_id,
            'feasibility_score': 100.0,
            'matched': [],
            'missing': [],
            'total_required': 0,
            'total_satisfied': 0
        }

    # Gather current user's owned inventory in-memory (read-only, no commit)
    owned_items = {}
    if user_id:
        user_inventory = (
            UserComponent.query.filter_by(user_id=user_id)
            .filter(UserComponent.quantity > 0)
            .all()
        )
        for uc in user_inventory:
            owned_items[uc.component_id] = {
                'name': uc.component_name,
                'quantity': uc.quantity
            }

        # Include any available components directly listed by this user
        user_listed = Component.query.filter_by(user_id=user_id, status='Available').filter(Component.quantity > 0).all()
        for lc in user_listed:
            if lc.id in owned_items:
                owned_items[lc.id]['quantity'] = max(owned_items[lc.id]['quantity'], lc.quantity)
            else:
                owned_items[lc.id] = {
                    'name': lc.name,
                    'quantity': lc.quantity
                }

    matched = []
    missing = []
    total_required = 0
    total_satisfied = 0

    for req in required_components:
        total_required += req.required_quantity

        # Find total quantity of this required part owned by current user
        available_qty = sum(
            item['quantity'] for item in owned_items.values()
            if names_match(item['name'], req.component_name)
        )

        satisfied = min(available_qty, req.required_quantity)
        total_satisfied += satisfied

        if satisfied >= req.required_quantity:
            matched.append({
                'name': req.component_name,
                'category': req.category or '',
                'required': req.required_quantity,
                'available': available_qty,
                'status': 'available'
            })
        elif satisfied > 0:
            matched.append({
                'name': req.component_name,
                'category': req.category or '',
                'required': req.required_quantity,
                'available': available_qty,
                'status': 'partial'
            })
            missing.append({
                'name': req.component_name,
                'category': req.category or '',
                'required': req.required_quantity,
                'available': available_qty,
                'needed': req.required_quantity - available_qty
            })
        else:
            missing.append({
                'name': req.component_name,
                'category': req.category or '',
                'required': req.required_quantity,
                'available': 0,
                'needed': req.required_quantity
            })

    feasibility = (total_satisfied / total_required * 100) if total_required > 0 else 0

    return {
        'project_id': project_id,
        'feasibility_score': round(feasibility, 1),
        'matched': matched,
        'missing': missing,
        'total_required': total_required,
        'total_satisfied': total_satisfied
    }


def calculate_all_matches(user_id):
    """
    Calculate matching scores for all projects against a user's components.
    Returns a list of match results sorted by feasibility score (descending).
    """
    projects = Project.query.all()
    results = []

    for project in projects:
        result = find_matching_components(user_id, project.id)
        if result:
            result['project'] = project
            results.append(result)

    # Sort by feasibility score descending, then by waste reduction
    results.sort(
        key=lambda x: (x['feasibility_score'], x['project'].estimated_waste_reduction),
        reverse=True
    )
    return results


def save_match_result(user_id, project_id):
    """
    Calculate and save/update a match result in the database.
    Returns the match result dict.
    """
    result = find_matching_components(user_id, project_id)
    if not result:
        return None

    existing = Match.query.filter_by(user_id=user_id, project_id=project_id).first()
    if existing:
        existing.feasibility_score = result['feasibility_score']
        existing.matched_components = json.dumps(result['matched'])
        existing.missing_components = json.dumps(result['missing'])
    else:
        match = Match(
            user_id=user_id,
            project_id=project_id,
            feasibility_score=result['feasibility_score'],
            matched_components=json.dumps(result['matched']),
            missing_components=json.dumps(result['missing'])
        )
        db.session.add(match)

    db.session.commit()
    return result


def save_all_matches(user_id):
    """Calculate and save matches for all projects for a user."""
    projects = Project.query.all()
    for project in projects:
        save_match_result(user_id, project.id)


def get_top_recommendations(user_id, limit=5):
    """
    Get the top recommended projects for a user based on:
    1. Feasibility score (higher is better)
    2. Available required components
    3. Waste reduction potential
    """
    all_matches = calculate_all_matches(user_id)

    # Filter to only projects with some feasibility (> 0)
    recommendations = [m for m in all_matches if m['feasibility_score'] > 0]

    return recommendations[:limit]


def get_feasibility_label(score):
    """Return a human-readable feasibility label and CSS class."""
    if score >= 80:
        return 'Highly Feasible', 'success'
    elif score >= 50:
        return 'Partially Feasible', 'warning'
    elif score > 0:
        return 'Low Feasibility', 'danger'
    else:
        return 'Not Feasible', 'secondary'
