from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    components = db.relationship('Component', foreign_keys='Component.user_id', backref='owner', lazy=True, cascade='all, delete-orphan')
    saved_projects = db.relationship('SavedProject', backref='user', lazy=True, cascade='all, delete-orphan')
    matches = db.relationship('Match', backref='user', lazy=True, cascade='all, delete-orphan')
    reuse_history = db.relationship('ReuseHistory', backref='user', lazy=True, cascade='all, delete-orphan')
    cart_items = db.relationship('CartItem', backref='user', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='user', lazy=True, cascade='all, delete-orphan')
    inventory = db.relationship('UserComponent', backref='user', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.name}>'


class Component(db.Model):
    __tablename__ = 'components'

    CATEGORIES = [
        'Microcontroller', 'Sensor', 'Motor', 'Display', 'Power',
        'Communication', 'Computer Part', 'Cable', 'PCB', 'Other'
    ]
    CONDITIONS = [
        'New', 'Used - Like New', 'Used - Good', 'Used - Fair', 'For Parts',
        'Good', 'Used', 'Damaged', 'Salvage'
    ]
    STATUSES = ['Available', 'Reserved', 'Used', 'Out of Stock']

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, default=0.0)
    condition = db.Column(db.String(30), default='Good')
    description = db.Column(db.Text)
    estimated_weight = db.Column(db.Float, default=0)
    image = db.Column(db.String(200))
    status = db.Column(db.String(20), default='Available')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    seller = db.relationship('User', foreign_keys=[seller_id], backref=db.backref('seller_components', lazy=True), lazy=True)
    reuse_history = db.relationship('ReuseHistory', backref='component', lazy=True)
    cart_items = db.relationship('CartItem', backref='component', lazy=True, cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', backref='component', lazy=True)
    user_components = db.relationship('UserComponent', backref='component', lazy=True, cascade='all, delete-orphan')

    @property
    def seller_name(self):
        """Return public seller name without disclosing private personal information."""
        if self.seller and self.seller.name:
            return self.seller.name
        if self.owner and self.owner.name:
            return self.owner.name
        return 'Verified Seller'

    @property
    def is_in_stock(self):
        return (self.quantity or 0) > 0 and self.status == 'Available'


    def __repr__(self):
        return f'<Component {self.name}>'


class Project(db.Model):
    __tablename__ = 'projects'

    CATEGORIES = [
        'IoT', 'Robotics', 'Education', 'Automation',
        'Smart Home', 'Creative', 'Electronics'
    ]
    DIFFICULTIES = ['Beginner', 'Intermediate', 'Advanced']

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    difficulty = db.Column(db.String(20))
    estimated_cost = db.Column(db.Float, default=0)
    estimated_waste_reduction = db.Column(db.Float, default=0)
    image = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    required_components = db.relationship('ProjectComponent', backref='project', lazy=True, cascade='all, delete-orphan')
    saved_by = db.relationship('SavedProject', backref='project', lazy=True, cascade='all, delete-orphan')
    matches = db.relationship('Match', backref='project', lazy=True, cascade='all, delete-orphan')
    reuse_history = db.relationship('ReuseHistory', backref='project', lazy=True)

    def __repr__(self):
        return f'<Project {self.title}>'


class ProjectComponent(db.Model):
    __tablename__ = 'project_components'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    component_name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50))
    required_quantity = db.Column(db.Integer, default=1)

    def __repr__(self):
        return f'<ProjectComponent {self.component_name} x{self.required_quantity}>'


class SavedProject(db.Model):
    __tablename__ = 'saved_projects'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SavedProject user={self.user_id} project={self.project_id}>'


class Match(db.Model):
    __tablename__ = 'matches'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    feasibility_score = db.Column(db.Float, default=0)
    matched_components = db.Column(db.Text)   # JSON string
    missing_components = db.Column(db.Text)    # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Match user={self.user_id} project={self.project_id} score={self.feasibility_score}>'


class ReuseHistory(db.Model):
    __tablename__ = 'reuse_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey('components.id'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    waste_reduced = db.Column(db.Float, default=0)
    reused_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ReuseHistory user={self.user_id} waste={self.waste_reduced}g>'


class CartItem(db.Model):
    __tablename__ = 'cart_items'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey('components.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def subtotal(self):
        unit_price = self.component.price if self.component and self.component.price else 0.0
        return unit_price * self.quantity

    def __repr__(self):
        return f'<CartItem user={self.user_id} comp={self.component_id} qty={self.quantity}>'


class Order(db.Model):
    __tablename__ = 'orders'

    STATUSES = ['Pending', 'Confirmed', 'Processing', 'Shipped', 'Delivered', 'Cancelled']
    PAYMENT_METHODS = ['Razorpay', 'UPI', 'Card', 'Cash on Delivery', 'Demo Payment']
    PAYMENT_STATUSES = ['Pending', 'Paid', 'Failed', 'Refunded']

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_amount = db.Column(db.Float, default=0.0, nullable=False)
    status = db.Column(db.String(30), default='Confirmed', nullable=False)
    payment_method = db.Column(db.String(50), default='Demo Payment', nullable=False)
    payment_status = db.Column(db.String(50), default='Pending', nullable=False)
    razorpay_order_id = db.Column(db.String(100), nullable=True)
    razorpay_payment_id = db.Column(db.String(100), nullable=True)
    razorpay_signature = db.Column(db.String(255), nullable=True)
    customer_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Order {self.order_number} total=₹{self.total_amount} status={self.status} payment={self.payment_status}>'


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    component_id = db.Column(db.Integer, db.ForeignKey('components.id'), nullable=True)
    component_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    unit_price = db.Column(db.Float, default=0.0, nullable=False)
    subtotal = db.Column(db.Float, default=0.0, nullable=False)
    status = db.Column(db.String(30), default='Confirmed', nullable=False)

    seller = db.relationship('User', foreign_keys=[seller_id], backref=db.backref('sold_order_items', lazy=True), lazy=True)

    @property
    def platform_fee(self):
        """Platform commission (5%)."""
        return round(self.subtotal * 0.05, 2)

    @property
    def seller_earnings(self):
        """Net amount attributed to seller."""
        return round(self.subtotal - self.platform_fee, 2)

    @property
    def seller_name(self):
        return self.seller.name if self.seller else 'Platform Seller'

    def __repr__(self):
        return f'<OrderItem {self.component_name} x{self.quantity} @ ₹{self.unit_price} seller={self.seller_id}>'



class UserComponent(db.Model):
    __tablename__ = 'user_components'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey('components.id'), nullable=False)
    quantity = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'component_id', name='uq_user_component'),
        db.CheckConstraint('quantity >= 0', name='ck_user_component_quantity'),
    )

    @property
    def component_name(self):
        return self.component.name if self.component else 'Unknown Component'

    @classmethod
    def add_or_update(cls, user_id, component_id, quantity):
        """Increase owned quantity for a user and component."""
        item = cls.query.filter_by(user_id=user_id, component_id=component_id).first()
        if item:
            item.quantity += quantity
            item.updated_at = datetime.utcnow()
        else:
            item = cls(user_id=user_id, component_id=component_id, quantity=quantity)
            db.session.add(item)
        return item

    @classmethod
    def consume(cls, user_id, component_id, quantity):
        """Consume owned quantity, never going below zero."""
        item = cls.query.filter_by(user_id=user_id, component_id=component_id).first()
        if not item or item.quantity < quantity:
            raise ValueError(f"Insufficient inventory to consume {quantity} units.")
        item.quantity -= quantity
        item.updated_at = datetime.utcnow()
        return item

    def __repr__(self):
        return f'<UserComponent user={self.user_id} comp={self.component_id} qty={self.quantity}>'

