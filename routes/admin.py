"""Admin routes: dashboard, user management, project management."""

import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from models.models import db, User, Component, Project, ProjectComponent, Match, ReuseHistory, Order, OrderItem
from services.waste_calculator import get_platform_stats, format_weight
from utils import admin_required, allowed_file

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@admin_required
def admin_dashboard():
    """Admin dashboard with platform-wide statistics."""
    total_users = User.query.count()
    total_components = Component.query.count()
    total_projects = Project.query.count()
    total_matches = Match.query.count()

    platform_stats = get_platform_stats()

    # Components by category
    categories = {}
    components = Component.query.all()
    for c in components:
        categories[c.category] = categories.get(c.category, 0) + 1

    # Components by condition
    conditions = {}
    for c in components:
        conditions[c.condition] = conditions.get(c.condition, 0) + 1

    # Components by status
    statuses = {}
    for c in components:
        statuses[c.status] = statuses.get(c.status, 0) + 1

    # Project popularity (by saves)
    project_popularity = {}
    projects = Project.query.all()
    for p in projects:
        save_count = len(p.saved_by)
        if save_count > 0:
            project_popularity[p.title] = save_count

    # Recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()

    return render_template(
        'admin_dashboard.html',
        total_users=total_users,
        total_components=total_components,
        total_projects=total_projects,
        total_matches=total_matches,
        platform_stats=platform_stats,
        categories=categories,
        conditions=conditions,
        statuses=statuses,
        project_popularity=project_popularity,
        recent_users=recent_users,
        format_weight=format_weight
    )


@admin_bp.route('/users')
@admin_required
def admin_users():
    """List all users."""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', users=users)


@admin_bp.route('/components')
@admin_required
def admin_components():
    """List all components for admin management."""
    components = Component.query.order_by(Component.created_at.desc()).all()
    return render_template('admin_components.html', components=components)


@admin_bp.route('/components/<int:component_id>/delete', methods=['POST'])
@admin_required
def admin_delete_component(component_id):
    """Admin delete any component."""
    component = Component.query.get_or_404(component_id)

    if component.image:
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], component.image)
        if os.path.exists(image_path):
            os.remove(image_path)

    name = component.name
    db.session.delete(component)
    db.session.commit()
    flash(f'Component "{name}" deleted.', 'success')
    return redirect(url_for('admin.admin_components'))


@admin_bp.route('/projects')
@admin_required
def admin_projects():
    """List all projects for admin management."""
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('admin_projects.html', projects=projects)


@admin_bp.route('/projects/add', methods=['GET', 'POST'])
@admin_required
def admin_add_project():
    """Add a new project."""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '')
        difficulty = request.form.get('difficulty', 'Beginner')
        estimated_cost = request.form.get('estimated_cost', '0')
        estimated_waste_reduction = request.form.get('estimated_waste_reduction', '0')

        errors = []
        if not title:
            errors.append('Project title is required.')

        try:
            estimated_cost = float(estimated_cost)
        except ValueError:
            estimated_cost = 0
        try:
            estimated_waste_reduction = float(estimated_waste_reduction)
        except ValueError:
            estimated_waste_reduction = 0

        # Handle image upload
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and file.filename != '':
                if allowed_file(file.filename):
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    image_filename = f'{uuid.uuid4().hex}.{ext}'
                    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename)
                    file.save(upload_path)
                else:
                    errors.append('Invalid image format.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template(
                'admin_project_form.html',
                project=None,
                categories=Project.CATEGORIES,
                difficulties=Project.DIFFICULTIES,
                component_categories=Component.CATEGORIES
            )

        project = Project(
            title=title,
            description=description,
            category=category,
            difficulty=difficulty,
            estimated_cost=estimated_cost,
            estimated_waste_reduction=estimated_waste_reduction,
            image=image_filename
        )
        db.session.add(project)
        db.session.flush()  # Get the project ID

        # Process requirements
        req_names = request.form.getlist('req_name[]')
        req_categories = request.form.getlist('req_category[]')
        req_quantities = request.form.getlist('req_quantity[]')

        for i in range(len(req_names)):
            if req_names[i].strip():
                try:
                    qty = int(req_quantities[i]) if i < len(req_quantities) else 1
                except (ValueError, IndexError):
                    qty = 1
                cat = req_categories[i] if i < len(req_categories) else ''

                pc = ProjectComponent(
                    project_id=project.id,
                    component_name=req_names[i].strip(),
                    category=cat,
                    required_quantity=qty
                )
                db.session.add(pc)

        db.session.commit()
        flash(f'Project "{title}" created successfully!', 'success')
        return redirect(url_for('admin.admin_projects'))

    return render_template(
        'admin_project_form.html',
        project=None,
        categories=Project.CATEGORIES,
        difficulties=Project.DIFFICULTIES,
        component_categories=Component.CATEGORIES
    )


@admin_bp.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_project(project_id):
    """Edit an existing project."""
    project = Project.query.get_or_404(project_id)

    if request.method == 'POST':
        project.title = request.form.get('title', '').strip()
        project.description = request.form.get('description', '').strip()
        project.category = request.form.get('category', '')
        project.difficulty = request.form.get('difficulty', 'Beginner')

        try:
            project.estimated_cost = float(request.form.get('estimated_cost', '0'))
        except ValueError:
            project.estimated_cost = 0
        try:
            project.estimated_waste_reduction = float(request.form.get('estimated_waste_reduction', '0'))
        except ValueError:
            project.estimated_waste_reduction = 0

        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and file.filename != '':
                if allowed_file(file.filename):
                    if project.image:
                        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], project.image)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    image_filename = f'{uuid.uuid4().hex}.{ext}'
                    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename)
                    file.save(upload_path)
                    project.image = image_filename

        # Update requirements - remove old ones and add new
        ProjectComponent.query.filter_by(project_id=project.id).delete()

        req_names = request.form.getlist('req_name[]')
        req_categories = request.form.getlist('req_category[]')
        req_quantities = request.form.getlist('req_quantity[]')

        for i in range(len(req_names)):
            if req_names[i].strip():
                try:
                    qty = int(req_quantities[i]) if i < len(req_quantities) else 1
                except (ValueError, IndexError):
                    qty = 1
                cat = req_categories[i] if i < len(req_categories) else ''

                pc = ProjectComponent(
                    project_id=project.id,
                    component_name=req_names[i].strip(),
                    category=cat,
                    required_quantity=qty
                )
                db.session.add(pc)

        db.session.commit()
        flash(f'Project "{project.title}" updated successfully!', 'success')
        return redirect(url_for('admin.admin_projects'))

    requirements = ProjectComponent.query.filter_by(project_id=project.id).all()

    return render_template(
        'admin_project_form.html',
        project=project,
        requirements=requirements,
        categories=Project.CATEGORIES,
        difficulties=Project.DIFFICULTIES,
        component_categories=Component.CATEGORIES
    )


@admin_bp.route('/projects/<int:project_id>/delete', methods=['POST'])
@admin_required
def admin_delete_project(project_id):
    """Delete a project."""
    project = Project.query.get_or_404(project_id)

    if project.image:
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], project.image)
        if os.path.exists(image_path):
            os.remove(image_path)

    title = project.title
    db.session.delete(project)
    db.session.commit()
    flash(f'Project "{title}" deleted.', 'success')
    return redirect(url_for('admin.admin_projects'))


# ─── ADMIN MARKETPLACE MANAGEMENT ───

@admin_bp.route('/orders')
@admin_required
def admin_orders():
    """List all orders for admin review."""
    status_filter = request.args.get('status', '')
    query = Order.query

    if status_filter:
        query = query.filter_by(status=status_filter)

    orders = query.order_by(Order.created_at.desc()).all()
    total_revenue = sum(o.total_amount for o in Order.query.filter(Order.status != 'Cancelled').all())

    return render_template(
        'admin_orders.html',
        orders=orders,
        status_filter=status_filter,
        statuses=Order.STATUSES,
        total_revenue=total_revenue
    )


@admin_bp.route('/orders/<int:order_id>')
@admin_required
def admin_order_detail(order_id):
    """View full order detail for admin."""
    order = Order.query.get_or_404(order_id)
    return render_template('admin_order_detail.html', order=order, statuses=Order.STATUSES)


@admin_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def admin_update_order_status(order_id):
    """Update order status."""
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')

    if new_status in Order.STATUSES:
        old_status = order.status
        order.status = new_status
        db.session.commit()
        flash(f'Order #{order.order_number} status updated from {old_status} to {new_status}.', 'success')
    else:
        flash('Invalid order status.', 'danger')

    return redirect(request.referrer or url_for('admin.admin_orders'))


@admin_bp.route('/components/<int:component_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_component(component_id):
    """Admin edit component price, available stock, condition, etc."""
    component = Component.query.get_or_404(component_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        price = request.form.get('price', '0')
        quantity = request.form.get('quantity', '1')
        condition = request.form.get('condition', 'Good')
        status = request.form.get('status', 'Available')
        category = request.form.get('category', component.category)
        description = request.form.get('description', '').strip()

        errors = []
        if not name:
            errors.append('Component name cannot be empty.')
        try:
            price = float(price)
            if price < 0:
                errors.append('Price cannot be negative.')
        except ValueError:
            errors.append('Price must be a valid number.')
            price = component.price or 0.0

        try:
            quantity = int(quantity)
            if quantity < 0:
                errors.append('Quantity cannot be negative.')
        except ValueError:
            errors.append('Quantity must be an integer.')
            quantity = component.quantity or 0

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template(
                'admin_component_edit.html',
                component=component,
                categories=Component.CATEGORIES,
                conditions=Component.CONDITIONS,
                statuses=Component.STATUSES
            )

        component.name = name
        component.price = price
        component.quantity = quantity
        component.condition = condition
        component.status = status
        component.category = category
        component.description = description
        db.session.commit()

        flash(f'Component "{component.name}" updated successfully (Price: ₹{price:.0f}, Stock: {quantity}).', 'success')
        return redirect(url_for('admin.admin_components'))

    return render_template(
        'admin_component_edit.html',
        component=component,
        categories=Component.CATEGORIES,
        conditions=Component.CONDITIONS,
        statuses=Component.STATUSES
    )
