"""
Marketplace Routes:
- Shopping Cart: view, add, update, remove, buy-now
- Checkout: order creation, simulated payment, inventory reduction
- Orders: user order history, order details, order confirmation
"""

import time
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.models import db, User, Component, CartItem, Order, OrderItem, UserComponent
from utils import login_required, format_currency
from services.payment import create_payment_order, verify_payment_signature, is_demo_mode

marketplace_bp = Blueprint('marketplace', __name__)


def generate_order_number():
    """Generate a unique human-readable order number, guaranteed not to collide."""
    last_order = Order.query.order_by(Order.id.desc()).first()
    next_num = (last_order.id + 1) if last_order else (Order.query.count() + 1)
    num = 1000 + next_num
    order_number = f'SL{num}'
    while Order.query.filter_by(order_number=order_number).first():
        num += 1
        order_number = f'SL{num}'
    return order_number



# ─── SHOPPING CART ───

@marketplace_bp.route('/cart')
@login_required
def view_cart():
    """Display user's shopping cart."""
    user_id = session['user_id']
    items = CartItem.query.filter_by(user_id=user_id).all()

    subtotal = sum(item.subtotal for item in items)
    delivery_fee = 0.0  # Free delivery for demo
    total = subtotal + delivery_fee

    return render_template(
        'cart.html',
        items=items,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total=total
    )


@marketplace_bp.route('/cart/add/<int:component_id>', methods=['POST'])
@login_required
def add_to_cart(component_id):
    """Add a component to the user's cart."""
    component = Component.query.get_or_404(component_id)
    user_id = session['user_id']

    # Seller cannot buy own listing
    if (component.seller_id and component.seller_id == user_id) or (component.user_id == user_id):
        msg = 'You cannot purchase your own component listing.'
        if request.is_json:
            return jsonify({'success': False, 'message': msg}), 400
        flash(msg, 'warning')
        return redirect(request.referrer or url_for('components.component_list'))

    # Read requested quantity
    try:
        if request.is_json:
            data = request.get_json() or {}
            qty = int(data.get('quantity', 1))
        else:
            qty = int(request.form.get('quantity', 1))
    except (ValueError, TypeError):
        qty = 1

    if qty < 1:
        qty = 1

    # Check available stock
    available_stock = component.quantity or 0
    if available_stock <= 0:
        msg = f'Sorry, "{component.name}" is currently out of stock.'
        if request.is_json:
            return jsonify({'success': False, 'message': msg}), 400
        flash(msg, 'warning')
        return redirect(request.referrer or url_for('components.component_list'))

    # Check existing item in user cart
    cart_item = CartItem.query.filter_by(user_id=user_id, component_id=component.id).first()

    if cart_item:
        new_qty = cart_item.quantity + qty
        if new_qty > available_stock:
            cart_item.quantity = available_stock
            db.session.commit()
            msg = f'Only {available_stock} units of "{component.name}" available. Cart updated to maximum available stock.'
            if request.is_json:
                return jsonify({'success': True, 'message': msg, 'cart_qty': available_stock})
            flash(msg, 'info')
            return redirect(url_for('marketplace.view_cart'))
        else:
            cart_item.quantity = new_qty
    else:
        if qty > available_stock:
            qty = available_stock
            flash(f'Requested quantity exceeded stock. Added maximum available: {qty} units.', 'info')
        cart_item = CartItem(user_id=user_id, component_id=component.id, quantity=qty)
        db.session.add(cart_item)

    db.session.commit()
    msg = f'Added {qty} × "{component.name}" to cart!'
    if request.is_json:
        total_count = sum(i.quantity for i in CartItem.query.filter_by(user_id=user_id).all())
        return jsonify({'success': True, 'message': msg, 'cart_count': total_count})

    flash(msg, 'success')
    return redirect(request.referrer or url_for('marketplace.view_cart'))


@marketplace_bp.route('/cart/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart_item(item_id):
    """Update quantity for a cart item."""
    cart_item = CartItem.query.get_or_404(item_id)

    # Security check: owner only
    if cart_item.user_id != session['user_id']:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('marketplace.view_cart'))

    action = request.form.get('action')
    stock = cart_item.component.quantity or 0

    if action == 'increase':
        if cart_item.quantity < stock:
            cart_item.quantity += 1
            db.session.commit()
            flash(f'Increased quantity of {cart_item.component.name}.', 'success')
        else:
            flash(f'Cannot add more. Only {stock} units in stock.', 'warning')
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            db.session.commit()
            flash(f'Decreased quantity of {cart_item.component.name}.', 'info')
        else:
            db.session.delete(cart_item)
            db.session.commit()
            flash(f'Removed {cart_item.component.name} from cart.', 'info')
    elif 'quantity' in request.form:
        try:
            new_qty = int(request.form.get('quantity'))
            if new_qty <= 0:
                db.session.delete(cart_item)
                flash(f'Removed {cart_item.component.name} from cart.', 'info')
            elif new_qty > stock:
                cart_item.quantity = stock
                flash(f'Clamped quantity to available stock ({stock} units).', 'warning')
            else:
                cart_item.quantity = new_qty
            db.session.commit()
        except ValueError:
            flash('Invalid quantity.', 'danger')

    return redirect(url_for('marketplace.view_cart'))


@marketplace_bp.route('/cart/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    """Remove an item from cart."""
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user_id != session['user_id']:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('marketplace.view_cart'))

    name = cart_item.component.name if cart_item.component else 'Item'
    db.session.delete(cart_item)
    db.session.commit()
    flash(f'"{name}" removed from cart.', 'info')
    return redirect(url_for('marketplace.view_cart'))


@marketplace_bp.route('/buy-now/<int:component_id>', methods=['POST'])
@login_required
def buy_now(component_id):
    """Instant purchase flow: sets quantity and goes straight to checkout."""
    component = Component.query.get_or_404(component_id)
    user_id = session['user_id']

    # Seller cannot buy own listing
    if (component.seller_id and component.seller_id == user_id) or (component.user_id == user_id):
        flash('You cannot purchase your own component listing.', 'warning')
        return redirect(request.referrer or url_for('components.component_list'))

    try:
        qty = int(request.form.get('quantity', 1))
    except (ValueError, TypeError):
        qty = 1

    if qty < 1:
        qty = 1

    stock = component.quantity or 0
    if stock <= 0:
        flash(f'"{component.name}" is currently out of stock.', 'warning')
        return redirect(url_for('components.component_detail', component_id=component.id))

    if qty > stock:
        qty = stock
        flash(f'Adjusted quantity to available stock ({stock} units).', 'info')

    # Add or update in cart
    cart_item = CartItem.query.filter_by(user_id=user_id, component_id=component.id).first()
    if cart_item:
        cart_item.quantity = qty
    else:
        cart_item = CartItem(user_id=user_id, component_id=component.id, quantity=qty)
        db.session.add(cart_item)

    db.session.commit()
    return redirect(url_for('marketplace.checkout'))


# ─── CHECKOUT & ORDERS ───

@marketplace_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Checkout page and order placement."""
    user_id = session['user_id']
    user = User.query.get(user_id)
    cart_items = CartItem.query.filter_by(user_id=user_id).all()

    if not cart_items:
        flash('Your cart is empty. Please add items before checking out.', 'warning')
        return redirect(url_for('components.component_list'))

    # Calculate fresh subtotal based on database component price
    subtotal = sum(item.component.price * item.quantity for item in cart_items if item.component)
    delivery_fee = 0.0
    total = subtotal + delivery_fee

    if request.method == 'POST':
        customer_name = request.form.get('customer_name', '').strip()
        email = request.form.get('email', '').strip() or user.email
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        pincode = request.form.get('pincode', '').strip()
        payment_method = request.form.get('payment_method', 'Demo Payment')

        errors = []
        if not customer_name:
            errors.append('Customer name is required.')
        if not phone:
            errors.append('Phone number is required.')
        if not address:
            errors.append('Delivery address is required.')
        if not city:
            errors.append('City is required.')
        if not state:
            errors.append('State is required.')
        if not pincode:
            errors.append('PIN code is required.')

        if payment_method not in Order.PAYMENT_METHODS:
            payment_method = 'Demo Payment'

        # Validate stock and seller ownership for every item before creating order
        for item in cart_items:
            comp = Component.query.get(item.component_id)
            if comp and ((comp.seller_id and comp.seller_id == user_id) or (comp.user_id == user_id)):
                errors.append(f'You cannot purchase your own listing ("{comp.name}"). Please remove it from your cart.')
            if not comp or comp.quantity < item.quantity:
                available = comp.quantity if comp else 0
                errors.append(
                    f'Insufficient stock for "{item.component.name}". Available: {available}, in cart: {item.quantity}.'
                )

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template(
                'checkout.html',
                cart_items=cart_items,
                subtotal=subtotal,
                delivery_fee=delivery_fee,
                total=total,
                user=user,
                customer_name=customer_name,
                email=email,
                phone=phone,
                address=address,
                city=city,
                state=state,
                pincode=pincode,
                payment_method=payment_method
            )

        # Generate unique human-readable order number e.g. #SL1001
        order_number = generate_order_number()
        payment_status = 'Pending' if payment_method == 'Cash on Delivery' else 'Paid'

        # Create Order
        order = Order(
            order_number=order_number,
            user_id=user_id,
            total_amount=total,
            status='Confirmed',
            payment_method=payment_method,
            payment_status=payment_status,
            customer_name=customer_name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            state=state,
            pincode=pincode
        )
        db.session.add(order)
        db.session.flush()

        # Create OrderItems and reduce component inventory
        try:
            for item in cart_items:
                comp = item.component
                unit_price = comp.price or 0.0
                item_subtotal = unit_price * item.quantity

                order_item = OrderItem(
                    order_id=order.id,
                    seller_id=(comp.seller_id or comp.user_id),
                    component_id=comp.id,
                    component_name=comp.name,
                    quantity=item.quantity,
                    unit_price=unit_price,
                    subtotal=item_subtotal,
                    status='Confirmed'
                )
                db.session.add(order_item)

                # Reduce inventory safely
                comp.quantity -= item.quantity
                if comp.quantity < 0:
                    comp.quantity = 0
                if comp.quantity == 0:
                    comp.status = 'Out of Stock'

                # Only credit user inventory when payment is Paid
                if payment_status == 'Paid':
                    UserComponent.add_or_update(user_id, comp.id, item.quantity)

                # Remove from user's cart
                db.session.delete(item)

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash('Failed to place order. Please try again.', 'danger')
            return redirect(url_for('marketplace.checkout'))

        flash(f'Order #{order.order_number} placed successfully! Thank you for reusing hardware.', 'success')
        return redirect(url_for('marketplace.order_success', order_id=order.id))

    return render_template(
        'checkout.html',
        cart_items=cart_items,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total=total,
        user=user
    )


# ─── RAZORPAY INTEGRATION ENDPOINTS ───

@marketplace_bp.route('/checkout/razorpay/create-order', methods=['POST'])
@login_required
def razorpay_create_order():
    """Create a Razorpay order or simulated demo order."""
    user_id = session['user_id']
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    if not cart_items:
        return jsonify({'success': False, 'error': 'Your cart is empty. Please add items before checking out.'}), 400

    # Stock and seller ownership validation
    for item in cart_items:
        comp = Component.query.get(item.component_id)
        if comp and ((comp.seller_id and comp.seller_id == user_id) or (comp.user_id == user_id)):
            return jsonify({
                'success': False,
                'error': f'You cannot purchase your own listing ("{comp.name}"). Please remove it from your cart.'
            }), 400
        if not comp or comp.quantity < item.quantity:
            avail = comp.quantity if comp else 0
            return jsonify({
                'success': False,
                'error': f'Insufficient stock for "{item.component.name}". Available: {avail}, in cart: {item.quantity}.'
            }), 400

    subtotal = sum((item.component.price or 0.0) * item.quantity for item in cart_items if item.component)
    delivery_fee = 0.0
    total = subtotal + delivery_fee

    temp_receipt = f"rcpt_{user_id}_{int(time.time())}"
    order_data = create_payment_order(
        amount_inr=total,
        receipt=temp_receipt,
        notes={'user_id': str(user_id)}
    )

    return jsonify({
        'success': True,
        'order_id': order_data['id'],
        'amount': order_data['amount'],
        'amount_inr': order_data['amount_inr'],
        'currency': order_data['currency'],
        'key_id': order_data['key_id'],
        'is_demo': order_data['is_demo']
    })


@marketplace_bp.route('/checkout/razorpay/verify', methods=['POST'])
@login_required
def razorpay_verify():
    """Verify Razorpay payment signature and persist order and inventory changes."""
    user_id = session['user_id']
    user = User.query.get(user_id)
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    if not cart_items:
        return jsonify({'success': False, 'error': 'Your cart is empty.'}), 400

    # Read payload from JSON or Form data
    data = request.get_json(silent=True) or request.form

    razorpay_order_id = data.get('razorpay_order_id', '').strip()
    razorpay_payment_id = data.get('razorpay_payment_id', '').strip()
    razorpay_signature = data.get('razorpay_signature', '').strip()

    customer_name = data.get('customer_name', '').strip()
    email = data.get('email', '').strip() or user.email
    phone = data.get('phone', '').strip()
    address = data.get('address', '').strip()
    city = data.get('city', '').strip()
    state = data.get('state', '').strip()
    pincode = data.get('pincode', '').strip()

    errors = []
    if not customer_name:
        errors.append('Customer name is required.')
    if not phone:
        errors.append('Phone number is required.')
    if not address:
        errors.append('Delivery address is required.')
    if not city:
        errors.append('City is required.')
    if not state:
        errors.append('State is required.')
    if not pincode:
        errors.append('PIN code is required.')
    if not razorpay_order_id or not razorpay_payment_id:
        errors.append('Payment transaction details are missing.')

    if errors:
        return jsonify({'success': False, 'error': ' '.join(errors)}), 400

    # Stock and seller ownership validation
    for item in cart_items:
        comp = Component.query.get(item.component_id)
        if comp and ((comp.seller_id and comp.seller_id == user_id) or (comp.user_id == user_id)):
            return jsonify({
                'success': False,
                'error': f'You cannot purchase your own listing ("{comp.name}"). Please remove it from your cart.'
            }), 400
        if not comp or comp.quantity < item.quantity:
            avail = comp.quantity if comp else 0
            return jsonify({
                'success': False,
                'error': f'Insufficient stock for "{item.component.name}". Available: {avail}, in cart: {item.quantity}.'
            }), 400

    # Signature verification
    is_valid, msg = verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)
    if not is_valid:
        return jsonify({'success': False, 'error': f'Payment verification failed: {msg}'}), 400

    # Compute totals
    subtotal = sum((item.component.price or 0.0) * item.quantity for item in cart_items if item.component)
    delivery_fee = 0.0
    total = subtotal + delivery_fee

    order_number = generate_order_number()

    order = Order(
        order_number=order_number,
        user_id=user_id,
        total_amount=total,
        status='Confirmed',
        payment_method='Razorpay',
        payment_status='Paid',
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        razorpay_signature=razorpay_signature,
        customer_name=customer_name,
        email=email,
        phone=phone,
        address=address,
        city=city,
        state=state,
        pincode=pincode
    )
    db.session.add(order)
    db.session.flush()

    try:
        for item in cart_items:
            comp = item.component
            unit_price = comp.price or 0.0
            item_subtotal = unit_price * item.quantity

            order_item = OrderItem(
                order_id=order.id,
                seller_id=(comp.seller_id or comp.user_id),
                component_id=comp.id,
                component_name=comp.name,
                quantity=item.quantity,
                unit_price=unit_price,
                subtotal=item_subtotal,
                status='Confirmed'
            )
            db.session.add(order_item)

            comp.quantity -= item.quantity
            if comp.quantity < 0:
                comp.quantity = 0
            if comp.quantity == 0:
                comp.status = 'Out of Stock'

            # Atomically credit buyer's personal inventory
            UserComponent.add_or_update(user_id, comp.id, item.quantity)

            db.session.delete(item)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Failed to finalize order: {str(e)}'}), 500

    flash(f'Payment successful! Order #{order.order_number} confirmed.', 'success')
    return jsonify({
        'success': True,
        'order_number': order.order_number,
        'order_id': order.id,
        'redirect_url': url_for('marketplace.order_success', order_id=order.id)
    })


@marketplace_bp.route('/api/webhook/razorpay', methods=['POST'])
def razorpay_webhook():
    """
    Idempotent webhook for Razorpay events:
    - payment.captured / order.paid: Finalize order, decrease stock, credit user inventory.
    - payment.failed: Mark order failed, do not decrease stock or credit inventory.
    """
    from services.payment import get_payment_config
    import json
    import os

    cfg = get_payment_config()
    webhook_secret = os.environ.get('RAZORPAY_WEBHOOK_SECRET', '')
    raw_payload = request.get_data()
    signature = request.headers.get('X-Razorpay-Signature', '')

    if webhook_secret:
        try:
            import razorpay
            client = razorpay.Client(auth=(cfg['key_id'], cfg['key_secret']))
            client.utility.verify_webhook_signature(raw_payload.decode('utf-8'), signature, webhook_secret)
        except Exception as e:
            return jsonify({'status': 'invalid signature', 'error': str(e)}), 400

    try:
        event = json.loads(raw_payload.decode('utf-8'))
    except Exception:
        return jsonify({'status': 'invalid json'}), 400

    event_type = event.get('event')
    payload = event.get('payload', {})

    if event_type in ('payment.captured', 'order.paid'):
        payment_entity = payload.get('payment', {}).get('entity', {})
        rzp_order_id = payment_entity.get('order_id')
        rzp_payment_id = payment_entity.get('id')

        if rzp_order_id:
            order = Order.query.filter_by(razorpay_order_id=rzp_order_id).first()
            if order and order.payment_status != 'Paid':
                order.payment_status = 'Paid'
                order.status = 'Confirmed'
                if rzp_payment_id:
                    order.razorpay_payment_id = rzp_payment_id

                for oi in order.items:
                    if oi.component_id:
                        comp = Component.query.get(oi.component_id)
                        if comp:
                            comp.quantity = max(0, comp.quantity - oi.quantity)
                            if comp.quantity == 0:
                                comp.status = 'Out of Stock'
                        UserComponent.add_or_update(order.user_id, oi.component_id, oi.quantity)
                db.session.commit()
                return jsonify({'status': 'order finalized'}), 200
            elif order and order.payment_status == 'Paid':
                return jsonify({'status': 'already processed'}), 200

    elif event_type == 'payment.failed':
        payment_entity = payload.get('payment', {}).get('entity', {})
        rzp_order_id = payment_entity.get('order_id')
        if rzp_order_id:
            order = Order.query.filter_by(razorpay_order_id=rzp_order_id).first()
            if order and order.payment_status != 'Paid':
                order.payment_status = 'Failed'
                db.session.commit()
                return jsonify({'status': 'order marked failed'}), 200

    return jsonify({'status': 'ok'}), 200




@marketplace_bp.route('/orders')
@marketplace_bp.route('/my-purchases')
@login_required
def my_orders():
    """User order / purchase history."""
    user_id = session['user_id']
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=orders)


@marketplace_bp.route('/my-sales')
@login_required
def my_sales():
    """List sales orders where the logged-in user is the seller."""
    user_id = session['user_id']
    sales_items = (
        OrderItem.query.filter_by(seller_id=user_id)
        .join(Order)
        .order_by(Order.created_at.desc())
        .all()
    )
    paid_sales = [it for it in sales_items if it.order and it.order.payment_status == 'Paid']
    total_sales_revenue = sum(it.subtotal for it in paid_sales)
    total_net_earnings = sum(it.seller_earnings for it in paid_sales)
    total_units_sold = sum(it.quantity for it in paid_sales)

    return render_template(
        'my_sales.html',
        sales_items=sales_items,
        total_sales_revenue=total_sales_revenue,
        total_net_earnings=total_net_earnings,
        total_units_sold=total_units_sold,
        format_currency=format_currency
    )


@marketplace_bp.route('/seller/orders/<int:item_id>/status', methods=['POST'])
@login_required
def update_sales_item_status(item_id):
    """Allow a seller or admin to update the order item fulfillment status."""
    item = OrderItem.query.get_or_404(item_id)
    user_id = session['user_id']

    # Security: Only the actual seller of this item or an admin can update its status
    if item.seller_id != user_id and session.get('user_role') != 'admin':
        flash('You are not authorized to update this sale item status.', 'danger')
        return redirect(url_for('marketplace.my_sales'))

    new_status = request.form.get('status')
    allowed_statuses = ['Confirmed', 'Processing', 'Shipped', 'Delivered', 'Cancelled']
    if new_status in allowed_statuses:
        item.status = new_status
        db.session.commit()
        flash(f'Fulfillment status for "{item.component_name}" updated to {new_status}.', 'success')
    else:
        flash('Invalid fulfillment status provided.', 'danger')

    return redirect(request.referrer or url_for('marketplace.my_sales'))


@marketplace_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    """View order details with RBAC security."""
    order = Order.query.get_or_404(order_id)

    # Security check: User can only see their own order, or seller if they sold an item in this order, or admin
    is_seller_of_item = any(item.seller_id == session['user_id'] for item in order.items)
    if order.user_id != session['user_id'] and not is_seller_of_item and session.get('user_role') != 'admin':
        flash('Access denied. You can only view your own orders or sales.', 'danger')
        return redirect(url_for('marketplace.my_orders'))

    return render_template('order_detail.html', order=order)


@marketplace_bp.route('/orders/<int:order_id>/success')
@login_required
def order_success(order_id):
    """Order confirmation screen."""
    order = Order.query.get_or_404(order_id)

    if order.user_id != session['user_id'] and session.get('user_role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('marketplace.my_orders'))

    return render_template('order_success.html', order=order)
