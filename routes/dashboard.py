"""Dashboard and matches routes."""

import json
from flask import Blueprint, render_template, session, redirect, url_for, flash
from models.models import db, Component, Project, SavedProject, Match, Order, OrderItem
from services.matching import (
    calculate_all_matches, get_top_recommendations,
    save_all_matches, get_feasibility_label
)
from services.waste_calculator import get_user_impact_stats, format_weight
from utils import login_required, format_currency

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard with stats, recommendations, impact, and seller analytics."""
    user_id = session['user_id']

    # Component stats
    my_components = Component.query.filter((Component.seller_id == user_id) | (Component.user_id == user_id)).all()
    available_components = [c for c in my_components if c.status == 'Available' and (c.quantity or 0) > 0]

    # Saved projects count
    saved_count = SavedProject.query.filter_by(user_id=user_id).count()

    # Marketplace buying stats
    my_orders = Order.query.filter_by(user_id=user_id).all()
    orders_count = len(my_orders)
    total_purchases = sum(sum(item.quantity for item in o.items) for o in my_orders if o.status != 'Cancelled')
    total_spent = sum(o.total_amount for o in my_orders if o.status != 'Cancelled')

    # Seller stats (Requirement 8)
    seller_items = OrderItem.query.filter_by(seller_id=user_id).all()
    paid_seller_items = [it for it in seller_items if it.order and it.order.payment_status == 'Paid']
    items_sold = sum(it.quantity for it in paid_seller_items)
    total_sales = sum(it.subtotal for it in paid_seller_items)
    active_listings_count = len(available_components)
    out_of_stock_count = len([c for c in my_components if (c.quantity or 0) <= 0 or c.status == 'Out of Stock'])
    pending_seller_orders = len([it for it in paid_seller_items if it.status not in ('Delivered', 'Cancelled')])

    # Get impact stats
    impact = get_user_impact_stats(user_id)

    # Get top recommendations
    recommendations = get_top_recommendations(user_id, limit=6)

    # Get recent components
    recent_components = Component.query.filter((Component.seller_id == user_id) | (Component.user_id == user_id))\
        .order_by(Component.created_at.desc()).limit(5).all()

    # Count matching projects (with score > 0)
    all_matches = calculate_all_matches(user_id)
    matching_projects = [m for m in all_matches if m['feasibility_score'] > 0]

    # Category breakdown for chart
    category_counts = {}
    for comp in my_components:
        category_counts[comp.category] = category_counts.get(comp.category, 0) + (comp.quantity or 0)

    return render_template(
        'dashboard.html',
        my_components=my_components,
        available_components=available_components,
        saved_count=saved_count,
        orders_count=orders_count,
        total_purchases=total_purchases,
        total_spent=total_spent,
        items_sold=items_sold,
        total_sales=total_sales,
        active_listings_count=active_listings_count,
        out_of_stock_count=out_of_stock_count,
        pending_seller_orders=pending_seller_orders,
        my_orders=my_orders,
        impact=impact,
        recommendations=recommendations,
        recent_components=recent_components,
        matching_count=len(matching_projects),
        category_counts=category_counts,
        get_feasibility_label=get_feasibility_label,
        format_weight=format_weight,
        format_currency=format_currency
    )


@dashboard_bp.route('/matches')
@login_required
def matches():
    """Show all project matches sorted by feasibility score."""
    user_id = session['user_id']

    # Calculate fresh matches
    all_matches = calculate_all_matches(user_id)

    # Also save them to database for persistence
    save_all_matches(user_id)

    return render_template(
        'matches.html',
        matches=all_matches,
        get_feasibility_label=get_feasibility_label,
        format_weight=format_weight
    )


@dashboard_bp.route('/matches/refresh')
@login_required
def refresh_matches():
    """Recalculate all matches for the current user."""
    user_id = session['user_id']
    save_all_matches(user_id)
    flash('Matches recalculated based on your current components!', 'success')
    return redirect(url_for('dashboard.matches'))
