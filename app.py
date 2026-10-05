"""
SECONDLIFE – E-Waste Reuse & Project Matching Platform
Main Flask Application
"""

import os
from datetime import timedelta
from dotenv import load_dotenv
from flask import Flask, render_template, session
from models.models import db, Component, Project, ReuseHistory, CartItem
from services.waste_calculator import format_weight
from utils import get_component_image, get_project_image, format_currency

# Load environment variables from .env file
load_dotenv()

# Import blueprints
from routes.auth import auth_bp
from routes.components import components_bp
from routes.projects import projects_bp
from routes.dashboard import dashboard_bp
from routes.admin import admin_bp
from routes.marketplace import marketplace_bp


def create_app():
    app = Flask(__name__)

    # Configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'secondlife-hackathon-secret-key-2024')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'database.db'))
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

    # Razorpay Payment Configuration
    app.config['RAZORPAY_KEY_ID'] = os.environ.get('RAZORPAY_KEY_ID', '')
    app.config['RAZORPAY_KEY_SECRET'] = os.environ.get('RAZORPAY_KEY_SECRET', '')
    app.config['RAZORPAY_WEBHOOK_SECRET'] = os.environ.get('RAZORPAY_WEBHOOK_SECRET', '')
    app.config['PAYMENT_MODE'] = os.environ.get('PAYMENT_MODE', 'demo').lower()
    app.config['PLATFORM_COMMISSION_PERCENTAGE'] = float(os.environ.get('PLATFORM_COMMISSION_PERCENTAGE', 5.0))

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize database
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(components_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(marketplace_bp)

    # Create all tables
    with app.app_context():
        db.create_all()

    # ─── Context Processor: inject globals into all templates ───
    @app.context_processor
    def inject_globals():
        cart_count = 0
        if 'user_id' in session:
            try:
                cart_count = sum(item.quantity for item in CartItem.query.filter_by(user_id=session['user_id']).all())
            except Exception:
                cart_count = 0
        return {
            'format_weight': format_weight,
            'format_currency': format_currency,
            'get_component_image': get_component_image,
            'get_project_image': get_project_image,
            'cart_count': cart_count,
            'razorpay_key_id': app.config.get('RAZORPAY_KEY_ID', ''),
            'payment_mode': app.config.get('PAYMENT_MODE', 'demo')
        }

    # ─── Home Route ───
    @app.route('/')
    def home():
        total_components = Component.query.filter_by(status='Available').count()
        total_projects = Project.query.count()
        total_reuses = ReuseHistory.query.count()
        total_waste = sum(h.waste_reduced for h in ReuseHistory.query.all())

        featured_projects = Project.query.order_by(Project.created_at.desc()).limit(6).all()
        featured_components = Component.query.filter_by(status='Available').order_by(Component.created_at.desc()).limit(4).all()

        return render_template(
            'index.html',
            total_components=total_components,
            total_projects=total_projects,
            total_reuses=total_reuses,
            total_waste=total_waste,
            featured_projects=featured_projects,
            featured_components=featured_components,
            format_weight=format_weight
        )

    # ─── Error Handlers ───
    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('500.html'), 500

    return app


# Create the app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
