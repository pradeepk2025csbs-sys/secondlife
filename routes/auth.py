"""Authentication routes: register, login, logout, profile."""

import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models.models import db, User
from utils import login_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        errors = []
        if not name:
            errors.append('Name is required.')
        if not email:
            errors.append('Email is required.')
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors.append('Please enter a valid email address.')
        if not password:
            errors.append('Password is required.')
        elif len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')

        # Check duplicate email
        if not errors:
            existing = User.query.filter_by(email=email).first()
            if existing:
                errors.append('An account with this email already exists.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html', name=name, email=email)

        # Create user
        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role='user'
        )
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('login.html', email=email)

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_email'] = user.email
            session['user_role'] = user.role
            session.permanent = True

            flash(f'Welcome back, {user.name}!', 'success')

            if user.role == 'admin':
                return redirect(url_for('admin.admin_dashboard'))
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
            return render_template('login.html', email=email)

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()

        errors = []
        if not name:
            errors.append('Name is required.')
        if not email:
            errors.append('Email is required.')

        # Check if email is taken by another user
        if email != user.email:
            existing = User.query.filter_by(email=email).first()
            if existing:
                errors.append('This email is already in use.')

        # Handle password change
        new_password = request.form.get('new_password', '')
        if new_password:
            if len(new_password) < 6:
                errors.append('New password must be at least 6 characters.')
            else:
                user.password_hash = generate_password_hash(new_password)

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('profile.html', user=user)

        user.name = name
        user.email = email
        db.session.commit()

        session['user_name'] = user.name
        session['user_email'] = user.email

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))

    from models.models import Order, OrderItem, Component, SavedProject, UserComponent
    my_purchases = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    my_listings = Component.query.filter((Component.seller_id == user.id) | (Component.user_id == user.id)).order_by(Component.created_at.desc()).all()
    my_sales_items = OrderItem.query.filter_by(seller_id=user.id).join(Order).order_by(Order.created_at.desc()).all()
    my_inventory_items = UserComponent.query.filter_by(user_id=user.id).filter(UserComponent.quantity > 0).all()
    my_saved_projects = SavedProject.query.filter_by(user_id=user.id).all()
    paid_sales = [it for it in my_sales_items if it.order and it.order.payment_status == 'Paid']
    total_sales_revenue = sum(it.subtotal for it in paid_sales)

    return render_template(
        'profile.html',
        user=user,
        my_purchases=my_purchases,
        my_listings=my_listings,
        my_sales_items=my_sales_items,
        my_inventory_items=my_inventory_items,
        my_saved_projects=my_saved_projects,
        total_sales_revenue=total_sales_revenue
    )
