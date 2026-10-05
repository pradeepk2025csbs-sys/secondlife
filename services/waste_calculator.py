"""
Waste Reduction Calculator for SECONDLIFE.
Tracks and calculates e-waste diverted through component reuse.
"""

from models.models import db, ReuseHistory, Component


def format_weight(grams):
    """Format weight in grams to a human-readable string."""
    if grams is None or grams == 0:
        return '0 g'
    if grams >= 1000:
        return f'{grams / 1000:.2f} kg'
    return f'{grams:.0f} g'


def calculate_user_waste_reduced(user_id):
    """Calculate total e-waste reduced by a specific user in grams."""
    history = ReuseHistory.query.filter_by(user_id=user_id).all()
    return sum(h.waste_reduced for h in history)


def calculate_total_waste_reduced():
    """Calculate total e-waste reduced across the entire platform in grams."""
    history = ReuseHistory.query.all()
    return sum(h.waste_reduced for h in history)


def get_user_impact_stats(user_id):
    """
    Get comprehensive environmental impact statistics for a user.

    Returns a dict with:
        - total_waste: total waste reduced in grams
        - formatted_waste: human-readable weight string
        - components_reused: number of components reused
        - projects_completed: number of unique projects completed
    """
    history = ReuseHistory.query.filter_by(user_id=user_id).all()
    total_waste = sum(h.waste_reduced for h in history)
    components_reused = len(history)
    projects_completed = len(set(h.project_id for h in history if h.project_id))

    return {
        'total_waste': total_waste,
        'formatted_waste': format_weight(total_waste),
        'components_reused': components_reused,
        'projects_completed': projects_completed
    }


def get_platform_stats():
    """
    Get platform-wide environmental impact statistics.

    Returns a dict with overall platform metrics.
    """
    all_history = ReuseHistory.query.all()
    total_waste = sum(h.waste_reduced for h in all_history)
    total_components_reused = len(all_history)
    total_projects_completed = len(set(
        (h.user_id, h.project_id) for h in all_history if h.project_id
    ))
    unique_users = len(set(h.user_id for h in all_history))

    return {
        'total_waste': total_waste,
        'formatted_waste': format_weight(total_waste),
        'total_components_reused': total_components_reused,
        'total_projects_completed': total_projects_completed,
        'unique_users': unique_users
    }


def estimate_project_waste_reduction(project):
    """
    Estimate the waste reduction for a project based on its required components.
    Uses the project's estimated_waste_reduction field.
    """
    return project.estimated_waste_reduction if project else 0
