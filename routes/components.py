"""Component CRUD routes: list, add, detail, edit, delete, sell, my-listings."""

import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify
from models.models import db, Component, UserComponent, User
from utils import login_required, allowed_file

components_bp = Blueprint('components', __name__)


@components_bp.route('/components')
def component_list():
    """List all available components with search, filter, and sort."""
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '')
    condition = request.args.get('condition', '')
    status = request.args.get('status', '')
    seller = request.args.get('seller', '').strip()
    min_price = request.args.get('min_price', '').strip()
    max_price = request.args.get('max_price', '').strip()
    availability = request.args.get('availability', '')
    sort = request.args.get('sort', 'newest')

    query = Component.query

    if search:
        query = query.filter(
            (Component.name.ilike(f'%{search}%')) |
            (Component.description.ilike(f'%{search}%'))
        )
    if category:
        query = query.filter_by(category=category)
    if condition:
        query = query.filter_by(condition=condition)
    if status:
        query = query.filter_by(status=status)

    if availability == 'in_stock':
        query = query.filter(Component.quantity > 0, Component.status == 'Available')
    elif availability == 'out_of_stock':
        query = query.filter((Component.quantity <= 0) | (Component.status == 'Out of Stock'))

    if seller:
        query = query.join(User, Component.seller_id == User.id).filter(User.name.ilike(f'%{seller}%'))

    if min_price:
        try:
            query = query.filter(Component.price >= float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            query = query.filter(Component.price <= float(max_price))
        except ValueError:
            pass

    if sort == 'price_asc':
        query = query.order_by(Component.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Component.price.desc())
    elif sort == 'name':
        query = query.order_by(Component.name.asc())
    elif sort == 'quantity':
        query = query.order_by(Component.quantity.desc())
    elif sort == 'weight':
        query = query.order_by(Component.estimated_weight.desc())
    else:  # newest
        query = query.order_by(Component.created_at.desc())

    components = query.all()

    return render_template(
        'components.html',
        components=components,
        search=search,
        category=category,
        condition=condition,
        status=status,
        seller=seller,
        min_price=min_price,
        max_price=max_price,
        availability=availability,
        sort=sort,
        categories=Component.CATEGORIES,
        conditions=Component.CONDITIONS,
        statuses=Component.STATUSES
    )


@components_bp.route('/sell', methods=['GET', 'POST'])
@components_bp.route('/components/add', methods=['GET', 'POST'])
@login_required
def add_component():
    """Add or sell a new component."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '')
        quantity = request.form.get('quantity', '1')
        price = request.form.get('price', '0')
        condition = request.form.get('condition', 'Good')
        estimated_weight = request.form.get('estimated_weight', '0')
        description = request.form.get('description', '').strip()

        # Validation
        errors = []
        if not name:
            errors.append('Component name is required.')
        if not category:
            errors.append('Category is required.')
        try:
            quantity = int(quantity)
            if quantity < 1:
                errors.append('Quantity must be at least 1.')
        except ValueError:
            errors.append('Quantity must be a valid number.')
            quantity = 1
        try:
            price = float(price)
            if price < 0:
                errors.append('Price cannot be negative.')
        except ValueError:
            errors.append('Price must be a valid number.')
            price = 0.0
        try:
            estimated_weight = float(estimated_weight)
            if estimated_weight < 0:
                errors.append('Weight cannot be negative.')
        except ValueError:
            errors.append('Weight must be a valid number.')
            estimated_weight = 0

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
                    errors.append('Invalid image format. Allowed: PNG, JPG, JPEG, WEBP.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template(
                'add_component.html',
                categories=Component.CATEGORIES,
                conditions=Component.CONDITIONS,
                name=name, category=category, quantity=quantity,
                price=price, condition=condition, estimated_weight=estimated_weight,
                description=description
            )

        component = Component(
            user_id=session['user_id'],
            seller_id=session['user_id'],
            name=name,
            category=category,
            quantity=quantity,
            price=price,
            condition=condition,
            estimated_weight=estimated_weight,
            description=description,
            image=image_filename,
            status='Available'
        )
        db.session.add(component)
        db.session.flush()

        # Add to user's personal inventory
        UserComponent.add_or_update(session['user_id'], component.id, component.quantity)
        db.session.commit()

        flash(f'Component "{name}" listed successfully in the marketplace!', 'success')
        return redirect(url_for('components.component_list'))

    return render_template(
        'add_component.html',
        categories=Component.CATEGORIES,
        conditions=Component.CONDITIONS
    )


@components_bp.route('/components/<int:component_id>')
def component_detail(component_id):
    """View component details."""
    component = Component.query.get_or_404(component_id)
    return render_template('component_detail.html', component=component)


@components_bp.route('/components/<int:component_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_component(component_id):
    """Edit a component (only owner, seller, or admin)."""
    component = Component.query.get_or_404(component_id)

    # Authorization check
    if component.user_id != session['user_id'] and (component.seller_id or 0) != session['user_id'] and session.get('user_role') != 'admin':
        flash('You are not authorized to edit this component.', 'danger')
        return redirect(url_for('components.component_list'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '')
        quantity = request.form.get('quantity', '1')
        price = request.form.get('price', str(component.price or 0.0))
        condition = request.form.get('condition', 'Good')
        status = request.form.get('status', 'Available')
        estimated_weight = request.form.get('estimated_weight', '0')
        description = request.form.get('description', '').strip()

        errors = []
        if not name:
            errors.append('Component name is required.')
        if not category:
            errors.append('Category is required.')
        try:
            quantity = int(quantity)
            if quantity < 1:
                errors.append('Quantity must be at least 1.')
        except ValueError:
            errors.append('Quantity must be a valid number.')
            quantity = 1
        try:
            price = float(price)
            if price < 0:
                errors.append('Price cannot be negative.')
        except ValueError:
            errors.append('Price must be a valid number.')
            price = component.price or 0.0
        try:
            estimated_weight = float(estimated_weight)
        except ValueError:
            estimated_weight = 0

        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and file.filename != '':
                if allowed_file(file.filename):
                    # Delete old image if exists
                    if component.image:
                        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], component.image)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    image_filename = f'{uuid.uuid4().hex}.{ext}'
                    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename)
                    file.save(upload_path)
                    component.image = image_filename
                else:
                    errors.append('Invalid image format. Allowed: PNG, JPG, JPEG, WEBP.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template(
                'edit_component.html',
                component=component,
                categories=Component.CATEGORIES,
                conditions=Component.CONDITIONS,
                statuses=Component.STATUSES
            )

        component.name = name
        component.category = category
        component.quantity = quantity
        component.price = price
        component.condition = condition
        component.status = status
        component.estimated_weight = estimated_weight
        component.description = description

        # Sync user's personal inventory
        uc = UserComponent.query.filter_by(user_id=component.user_id, component_id=component.id).first()
        if uc:
            uc.quantity = component.quantity if component.status == 'Available' else 0
        elif component.status == 'Available' and component.quantity > 0:
            UserComponent.add_or_update(component.user_id, component.id, component.quantity)

        db.session.commit()

        flash(f'Component "{name}" updated successfully!', 'success')
        return redirect(url_for('components.component_detail', component_id=component.id))

    return render_template(
        'edit_component.html',
        component=component,
        categories=Component.CATEGORIES,
        conditions=Component.CONDITIONS,
        statuses=Component.STATUSES
    )


@components_bp.route('/components/<int:component_id>/delete', methods=['POST'])
@login_required
def delete_component(component_id):
    """Delete a component (only owner, seller, or admin)."""
    component = Component.query.get_or_404(component_id)

    if component.user_id != session['user_id'] and (component.seller_id or 0) != session['user_id'] and session.get('user_role') != 'admin':
        flash('You are not authorized to delete this component.', 'danger')
        return redirect(url_for('components.component_list'))

    # Delete image file if exists
    if component.image:
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], component.image)
        if os.path.exists(image_path):
            os.remove(image_path)

    name = component.name
    # Remove from personal inventory
    UserComponent.query.filter_by(user_id=component.user_id, component_id=component.id).delete()
    db.session.delete(component)
    db.session.commit()

    flash(f'Component "{name}" deleted successfully.', 'success')
    return redirect(request.referrer or url_for('components.my_listings'))


@components_bp.route('/my-listings')
@login_required
def my_listings():
    """View and manage user's seller marketplace listings."""
    user_id = session['user_id']
    listings = (
        Component.query.filter(
            (Component.seller_id == user_id) | (Component.user_id == user_id)
        )
        .order_by(Component.created_at.desc())
        .all()
    )
    active_count = sum(1 for c in listings if c.quantity > 0 and c.status == 'Available')
    out_of_stock_count = sum(1 for c in listings if c.quantity == 0 or c.status == 'Out of Stock')

    return render_template(
        'my_listings.html',
        listings=listings,
        active_count=active_count,
        out_of_stock_count=out_of_stock_count
    )


@components_bp.route('/components/<int:component_id>/quick-update', methods=['POST'])
@login_required
def quick_update_component(component_id):
    """Quick update stock and price for a seller listing."""
    component = Component.query.get_or_404(component_id)
    user_id = session['user_id']

    # Security check: must be owner/seller or admin
    if component.user_id != user_id and (component.seller_id or 0) != user_id and session.get('user_role') != 'admin':
        if request.is_json:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        flash('You are not authorized to update this listing.', 'danger')
        return redirect(url_for('components.my_listings'))

    data = request.get_json(silent=True) or request.form
    new_stock = data.get('quantity')
    new_price = data.get('price')
    new_status = data.get('status')

    if new_stock is not None:
        try:
            qty = int(new_stock)
            if qty < 0:
                flash('Stock cannot be negative.', 'danger')
            else:
                component.quantity = qty
                # Auto update status according to requirement 21
                if qty == 0:
                    component.status = 'Out of Stock'
                elif component.status in ('Out of Stock', 'Reserved'):
                    component.status = 'Available'
        except (ValueError, TypeError):
            flash('Invalid stock quantity.', 'danger')

    if new_price is not None:
        try:
            pr = float(new_price)
            if pr < 0:
                flash('Price cannot be negative.', 'danger')
            else:
                component.price = pr
        except (ValueError, TypeError):
            flash('Invalid price.', 'danger')

    if new_status and new_status in Component.STATUSES:
        component.status = new_status

    # Sync personal inventory if applicable
    uc = UserComponent.query.filter_by(user_id=component.user_id, component_id=component.id).first()
    if uc:
        uc.quantity = component.quantity if component.status == 'Available' else 0

    db.session.commit()

    if request.is_json:
        return jsonify({
            'success': True,
            'quantity': component.quantity,
            'price': component.price,
            'status': component.status
        })

    flash(f'Listing "{component.name}" updated successfully.', 'success')
    return redirect(request.referrer or url_for('components.my_listings'))


@components_bp.route('/my-inventory')
@components_bp.route('/my-components')
@login_required
def my_inventory():
    """View user's personal inventory of available components."""
    user_id = session['user_id']

    # Sync any user-listed available components
    user_listed = Component.query.filter_by(user_id=user_id, status='Available').filter(Component.quantity > 0).all()
    for lc in user_listed:
        uc = UserComponent.query.filter_by(user_id=user_id, component_id=lc.id).first()
        if not uc:
            uc = UserComponent(user_id=user_id, component_id=lc.id, quantity=lc.quantity)
            db.session.add(uc)
        elif uc.quantity != lc.quantity:
            uc.quantity = lc.quantity
    db.session.commit()

    inventory_items = (
        UserComponent.query.filter_by(user_id=user_id)
        .filter(UserComponent.quantity > 0)
        .all()
    )
    total_units = sum(item.quantity for item in inventory_items)
    total_types = len(inventory_items)

    return render_template(
        'inventory.html',
        inventory_items=inventory_items,
        total_units=total_units,
        total_types=total_types
    )
