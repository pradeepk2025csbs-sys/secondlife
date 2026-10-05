"""Project routes: list, detail, save/unsave, complete, saved list."""

import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.models import db, Project, ProjectComponent, SavedProject, Component, ReuseHistory, UserComponent
from services.matching import find_matching_components, get_feasibility_label, names_match
from services.waste_calculator import format_weight
from utils import login_required

projects_bp = Blueprint('projects', __name__)


@projects_bp.route('/projects')
def project_list():
    """List all reuse projects with search and filter."""
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '')
    difficulty = request.args.get('difficulty', '')

    query = Project.query

    if search:
        query = query.filter(Project.title.ilike(f'%{search}%'))
    if category:
        query = query.filter_by(category=category)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)

    projects = query.order_by(Project.created_at.desc()).all()

    # If user is logged in, calculate feasibility for each project
    project_scores = {}
    if 'user_id' in session:
        for project in projects:
            result = find_matching_components(session['user_id'], project.id)
            if result:
                project_scores[project.id] = result['feasibility_score']

    return render_template(
        'projects.html',
        projects=projects,
        project_scores=project_scores,
        search=search,
        category=category,
        difficulty=difficulty,
        categories=Project.CATEGORIES,
        difficulties=Project.DIFFICULTIES
    )


@projects_bp.route('/projects/<int:project_id>')
def project_detail(project_id):
    """View project details with matching info for logged-in users."""
    project = Project.query.get_or_404(project_id)
    required = ProjectComponent.query.filter_by(project_id=project_id).all()

    match_result = None
    is_saved = False
    is_completed = False
    feasibility_label = ('Not Feasible', 'secondary')

    if 'user_id' in session:
        match_result = find_matching_components(session['user_id'], project_id)
        if match_result:
            feasibility_label = get_feasibility_label(match_result['feasibility_score'])

        saved = SavedProject.query.filter_by(
            user_id=session['user_id'],
            project_id=project_id
        ).first()
        is_saved = saved is not None

        completed = ReuseHistory.query.filter_by(
            user_id=session['user_id'],
            project_id=project_id
        ).first()
        is_completed = completed is not None

    return render_template(
        'project_detail.html',
        project=project,
        required=required,
        match_result=match_result,
        is_saved=is_saved,
        is_completed=is_completed,
        feasibility_label=feasibility_label,
        format_weight=format_weight
    )


@projects_bp.route('/projects/<int:project_id>/save', methods=['POST'])
@login_required
def save_project(project_id):
    """Save/bookmark a project."""
    project = Project.query.get_or_404(project_id)

    existing = SavedProject.query.filter_by(
        user_id=session['user_id'],
        project_id=project_id
    ).first()

    if existing:
        flash('Project is already in your saved list.', 'info')
    else:
        saved = SavedProject(
            user_id=session['user_id'],
            project_id=project_id
        )
        db.session.add(saved)
        db.session.commit()
        flash(f'"{project.title}" saved to your list!', 'success')

    return redirect(url_for('projects.project_detail', project_id=project_id))


@projects_bp.route('/projects/<int:project_id>/unsave', methods=['POST'])
@login_required
def unsave_project(project_id):
    """Remove a project from saved list."""
    saved = SavedProject.query.filter_by(
        user_id=session['user_id'],
        project_id=project_id
    ).first()

    if saved:
        db.session.delete(saved)
        db.session.commit()
        flash('Project removed from saved list.', 'info')

    return redirect(request.referrer or url_for('projects.project_list'))


@projects_bp.route('/projects/<int:project_id>/complete', methods=['POST'])
@login_required
def complete_project(project_id):
    """
    Mark a project as completed: reuse matched components and track waste reduction.
    This consumes the user's matching components and creates reuse history entries.
    """
    project = Project.query.get_or_404(project_id)
    user_id = session['user_id']

    # Prevent repeated completion
    existing_completion = ReuseHistory.query.filter_by(
        user_id=user_id,
        project_id=project_id
    ).first()
    if existing_completion:
        flash(f'You have already completed "{project.title}".', 'info')
        return redirect(url_for('projects.project_detail', project_id=project_id))

    match_result = find_matching_components(user_id, project_id)
    if not match_result:
        flash('Could not calculate match for this project.', 'danger')
        return redirect(url_for('projects.project_detail', project_id=project_id))

    if match_result['feasibility_score'] < 50:
        flash('Feasibility score is too low to complete this project. You need at least 50%.', 'warning')
        return redirect(url_for('projects.project_detail', project_id=project_id))

    required = ProjectComponent.query.filter_by(project_id=project_id).all()
    total_waste_reduced = 0

    # Sync any user-listed components before consumption
    user_listed = Component.query.filter_by(user_id=user_id, status='Available').filter(Component.quantity > 0).all()
    for lc in user_listed:
        uc_item = UserComponent.query.filter_by(user_id=user_id, component_id=lc.id).first()
        if not uc_item:
            uc_item = UserComponent(user_id=user_id, component_id=lc.id, quantity=lc.quantity)
            db.session.add(uc_item)
        elif uc_item.quantity != lc.quantity:
            uc_item.quantity = lc.quantity
    db.session.commit()

    for req in required:
        needed = req.required_quantity
        # Find matching user components from UserComponent
        user_inventory = (
            UserComponent.query.filter_by(user_id=user_id)
            .filter(UserComponent.quantity > 0)
            .all()
        )

        for uc in user_inventory:
            if needed <= 0:
                break
            if names_match(uc.component_name, req.component_name):
                use_qty = min(uc.quantity, needed)
                if use_qty <= 0:
                    continue

                comp = uc.component
                weight_each = (comp.estimated_weight or 20.0) if comp else 20.0
                waste = weight_each * use_qty

                # Create reuse history
                history = ReuseHistory(
                    user_id=user_id,
                    component_id=uc.component_id,
                    project_id=project_id,
                    waste_reduced=waste
                )
                db.session.add(history)
                total_waste_reduced += waste

                # Consume from UserComponent personal inventory
                uc.quantity = max(0, uc.quantity - use_qty)

                # Also if this was user's listed component in Component table, update it
                if comp and comp.user_id == user_id:
                    comp.quantity = max(0, comp.quantity - use_qty)
                    if comp.quantity == 0:
                        comp.status = 'Used'

                needed -= use_qty

    db.session.commit()

    flash(
        f'🎉 Project "{project.title}" completed! '
        f'You diverted {format_weight(total_waste_reduced)} of e-waste!',
        'success'
    )
    return redirect(url_for('dashboard.dashboard'))


@projects_bp.route('/saved-projects')
@login_required
def saved_projects():
    """List user's saved/bookmarked projects."""
    saved = SavedProject.query.filter_by(user_id=session['user_id'])\
        .order_by(SavedProject.created_at.desc()).all()

    projects_with_scores = []
    for sp in saved:
        match_result = find_matching_components(session['user_id'], sp.project_id)
        projects_with_scores.append({
            'saved': sp,
            'project': sp.project,
            'match': match_result
        })

    return render_template(
        'saved_projects.html',
        projects_with_scores=projects_with_scores
    )
