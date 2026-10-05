"""
SECONDLIFE Comprehensive Test Suite
Tests all routes, matching logic, waste calculation, authentication,
CRUD operations, admin access control, and edge cases.
"""

import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models.models import db, User, Component, Project, ProjectComponent, SavedProject, ReuseHistory, Match
from services.matching import find_matching_components, calculate_all_matches
from services.waste_calculator import get_user_impact_stats, get_platform_stats, format_weight


def run_tests():
    print("=" * 60)
    print("RUNNING SECONDLIFE SYSTEM TESTS")
    print("=" * 60)

    with app.test_client() as client:
        # 1. Test Home page
        print("\n[Test 1] Homepage & Public Routes")
        res = client.get('/')
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        assert b"SECONDLIFE" in res.data
        assert b"Give Your Electronics" in res.data
        print("  ✓ Homepage loads successfully (Status 200)")

        res = client.get('/components')
        assert res.status_code == 200
        assert b"Electronic Components" in res.data
        print("  ✓ Public components list loads successfully")

        res = client.get('/projects')
        assert res.status_code == 200
        assert b"Reuse Projects" in res.data
        print("  ✓ Public projects list loads successfully")

        # 2. Test Register & Login
        print("\n[Test 2] Authentication")
        # Login with seed account
        res = client.post('/login', data={
            'email': 'rahul@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        assert res.status_code == 200
        assert b"Dashboard" in res.data or b"Rahul" in res.data
        print("  ✓ Rahul Sharma logged in successfully")

        # 3. Test Dashboard
        print("\n[Test 3] User Dashboard")
        res = client.get('/dashboard')
        assert res.status_code == 200
        assert b"Dashboard" in res.data
        assert b"My Components" in res.data
        assert b"E-Waste Diverted" in res.data
        print("  ✓ Dashboard displays stats and impact metrics")

        # 4. Test Component CRUD
        print("\n[Test 4] Component CRUD")
        # Add component
        res = client.post('/components/add', data={
            'name': 'Test ESP32 Board',
            'category': 'Microcontroller',
            'quantity': '2',
            'condition': 'New',
            'estimated_weight': '20',
            'description': 'Dual-core WiFi and Bluetooth board for testing'
        }, follow_redirects=True)
        assert res.status_code == 200
        assert b"added successfully" in res.data

        with app.app_context():
            test_comp = Component.query.filter_by(name='Test ESP32 Board').first()
            assert test_comp is not None
            assert test_comp.quantity == 2
            assert test_comp.estimated_weight == 20.0
            test_comp_id = test_comp.id
            print(f"  ✓ Component created in database (ID: {test_comp_id})")

        # Component detail
        res = client.get(f'/components/{test_comp_id}')
        assert res.status_code == 200
        assert b"Test ESP32 Board" in res.data
        print("  ✓ Component detail page loads")

        # Edit component
        res = client.post(f'/components/{test_comp_id}/edit', data={
            'name': 'Test ESP32 Board Updated',
            'category': 'Microcontroller',
            'quantity': '5',
            'condition': 'Good',
            'status': 'Available',
            'estimated_weight': '22',
            'description': 'Updated description'
        }, follow_redirects=True)
        assert res.status_code == 200
        assert b"updated successfully" in res.data

        with app.app_context():
            test_comp = Component.query.get(test_comp_id)
            assert test_comp.name == 'Test ESP32 Board Updated'
            assert test_comp.quantity == 5
            print("  ✓ Component updated in database")

        # Delete component
        res = client.post(f'/components/{test_comp_id}/delete', follow_redirects=True)
        assert res.status_code == 200
        assert b"deleted successfully" in res.data

        with app.app_context():
            test_comp = Component.query.get(test_comp_id)
            assert test_comp is None
            print("  ✓ Component deleted from database")

        # 5. Test Matching Engine & Feasibility
        print("\n[Test 5] Smart Matching Engine")
        with app.app_context():
            rahul = User.query.filter_by(email='rahul@example.com').first()
            # Ensure baseline components are Available for idempotent testing
            for c in rahul.components:
                c.status = 'Available'
                if c.quantity == 0:
                    c.quantity = 1
            db.session.commit()

            dustbin = Project.query.filter_by(title='Smart Dustbin').first()
            obstacle = Project.query.filter_by(title='Obstacle Avoiding Robot').first()

            # Match for Smart Dustbin
            match_dustbin = find_matching_components(rahul.id, dustbin.id)
            print(f"  Smart Dustbin Feasibility for Rahul: {match_dustbin['feasibility_score']}%")
            print(f"    - Matched: {[m['name'] for m in match_dustbin['matched']]}")
            print(f"    - Missing: {[m['name'] for m in match_dustbin['missing']]}")
            assert match_dustbin['feasibility_score'] == 100.0, "Expected 100% feasibility"

            # Match for Obstacle Avoiding Robot (requires DC Motor, Motor Driver, Battery which Rahul lacks)
            match_obstacle = find_matching_components(rahul.id, obstacle.id)
            print(f"  Obstacle Robot Feasibility for Rahul: {match_obstacle['feasibility_score']}%")
            print(f"    - Matched: {[m['name'] for m in match_obstacle['matched']]}")
            print(f"    - Missing: {[m['name'] for m in match_obstacle['missing']]}")
            assert 0 < match_obstacle['feasibility_score'] < 100.0, "Expected partial feasibility"

        # 6. Test Matches Page
        res = client.get('/matches')
        assert res.status_code == 200
        assert b"Smart Project Matches" in res.data
        print("  ✓ /matches page renders correctly with real scores")

        # 7. Test Save / Unsave Projects
        print("\n[Test 6] Saved Projects")
        with app.app_context():
            proj = Project.query.filter_by(title='Mini Security Alarm').first()
            proj_id = proj.id

        # Save project
        res = client.post(f'/projects/{proj_id}/save', follow_redirects=True)
        assert res.status_code == 200

        res = client.get('/saved-projects')
        assert res.status_code == 200
        assert b"Mini Security Alarm" in res.data
        print("  ✓ Project saved and appears in /saved-projects")

        # Test duplicate save prevention
        res = client.post(f'/projects/{proj_id}/save', follow_redirects=True)
        assert b"already in your saved list" in res.data
        print("  ✓ Duplicate project save prevented")

        # Unsave project
        res = client.post(f'/projects/{proj_id}/unsave', follow_redirects=True)
        assert res.status_code == 200

        with app.app_context():
            saved = SavedProject.query.filter_by(user_id=rahul.id, project_id=proj_id).first()
            assert saved is None
            print("  ✓ Project removed from saved list")

        # 8. Test Project Completion / Waste Tracking
        print("\n[Test 7] Project Completion & Waste Diverted")
        with app.app_context():
            # Reset Rahul's Smart Dustbin test completion & test components for repeatability
            ReuseHistory.query.filter_by(user_id=rahul.id, project_id=dustbin.id).delete()
            for comp_name in ['Arduino Uno', 'Ultrasonic Sensor', 'Servo Motor', 'Jumper Wires']:
                c = Component.query.filter_by(user_id=rahul.id, name=comp_name).first()
                if c:
                    c.status = 'Available'
                    if c.quantity == 0:
                        c.quantity = 1
            db.session.commit()
            prev_waste = sum(h.waste_reduced for h in ReuseHistory.query.filter_by(user_id=rahul.id).all())

        # Complete Smart Dustbin
        res = client.post(f'/projects/{dustbin.id}/complete', follow_redirects=True)
        assert res.status_code == 200
        assert b"completed" in res.data

        with app.app_context():
            new_waste = sum(h.waste_reduced for h in ReuseHistory.query.filter_by(user_id=rahul.id).all())
            assert new_waste > prev_waste, "Expected waste diverted to increase"
            print(f"  ✓ Project completed! Diverted waste increased from {prev_waste}g to {new_waste}g ({format_weight(new_waste)})")

        # 9. Test Authorization: Normal User Cannot Access Admin
        print("\n[Test 8] Role-Based Access Control")
        res = client.get('/admin/', follow_redirects=True)
        assert b"Admin privileges required" in res.data
        print("  ✓ Normal user denied access to /admin/")

        # 10. Logout & Admin Login
        client.get('/logout')
        res = client.post('/login', data={
            'email': 'admin@secondlife.com',
            'password': 'admin123'
        }, follow_redirects=True)
        assert res.status_code == 200
        assert b"Admin Dashboard" in res.data
        print("  ✓ Admin logged in successfully")

        # 11. Admin Pages
        print("\n[Test 9] Admin Pages & Management")
        res = client.get('/admin/')
        assert res.status_code == 200
        assert b"Total Users" in res.data
        assert b"Platform overview" in res.data
        print("  ✓ Admin dashboard renders with charts")

        res = client.get('/admin/users')
        assert res.status_code == 200
        assert b"User Management" in res.data
        print("  ✓ Admin users management page loads")

        res = client.get('/admin/components')
        assert res.status_code == 200
        assert b"Component Management" in res.data
        print("  ✓ Admin components management page loads")

        res = client.get('/admin/projects')
        assert res.status_code == 200
        assert b"Project Management" in res.data
        print("  ✓ Admin projects management page loads")

        # Admin add project
        res = client.post('/admin/projects/add', data={
            'title': 'Solar Powered Fan',
            'description': 'A portable cooling fan powered by a solar panel.',
            'category': 'Electronics',
            'difficulty': 'Beginner',
            'estimated_cost': '150',
            'estimated_waste_reduction': '180',
            'req_name[]': ['DC Motor', 'Solar Cell'],
            'req_category[]': ['Motor', 'Power'],
            'req_quantity[]': ['1', '1']
        }, follow_redirects=True)
        assert res.status_code == 200
        assert b"Solar Powered Fan" in res.data

        new_proj_id = None
        with app.app_context():
            new_proj = Project.query.filter_by(title='Solar Powered Fan').first()
            assert new_proj is not None
            assert len(new_proj.required_components) == 2
            new_proj_id = new_proj.id
            print("  ✓ Admin successfully created new project with requirements")

        # Clean up test project
        if new_proj_id:
            client.post(f'/admin/projects/{new_proj_id}/delete', follow_redirects=True)
            with app.app_context():
                deleted_proj = Project.query.get(new_proj_id)
                assert deleted_proj is None
                print("  ✓ Admin successfully deleted project")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY! (100% PASS RATE)")
    print("=" * 60)


if __name__ == '__main__':
    run_tests()
