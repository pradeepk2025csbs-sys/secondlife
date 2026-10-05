"""
Dedicated Integration Test Suite for SECONDLIFE
Integration: MARKETPLACE -> USER INVENTORY -> MATCHING ENGINE

Tests the 7 exact cases required:
Test 1: New user owns nothing. Expected feasibility = 0%.
Test 2: Buy one required component. Feasibility increases according to formula.
Test 3: Buy all required components. Feasibility = 100%.
Test 4: Buy 2 units of a component requiring 1. Requirement satisfied without exceeding percentage.
Test 5: Another user owns the component. Current user still shows 0%.
Test 6: Complete the project. Required components consumed from inventory, ReuseHistory created, never negative.
Test 7: Refresh / re-login. Inventory and feasibility remain correct and persisted.
"""

import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models.models import (
    db, User, Component, Project, ProjectComponent,
    UserComponent, ReuseHistory, Order, OrderItem, CartItem
)
from services.matching import find_matching_components


def run_inventory_matching_tests():
    print("=" * 70)
    print("RUNNING INVENTORY & MATCHING ENGINE INTEGRATION TESTS")
    print("=" * 70)

    with app.app_context():
        # Pre-cleanup in case of prior aborted run
        for email in ['inv_buyer1@example.com', 'inv_buyer2@example.com']:
            u = User.query.filter_by(email=email).first()
            if u:
                CartItem.query.filter_by(user_id=u.id).delete()
                orders = Order.query.filter_by(user_id=u.id).all()
                for o in orders:
                    OrderItem.query.filter_by(order_id=o.id).delete()
                    db.session.delete(o)
                UserComponent.query.filter_by(user_id=u.id).delete()
                ReuseHistory.query.filter_by(user_id=u.id).delete()
                db.session.delete(u)
        db.session.commit()

        # Ensure project 'Smart Dustbin' exists with requirements:
        # Arduino Uno (1), Ultrasonic Sensor (1), Servo Motor (1), Jumper Wires (1)
        dustbin = Project.query.filter_by(title='Smart Dustbin').first()
        assert dustbin is not None, "Project 'Smart Dustbin' not found"
        dustbin_id = dustbin.id

        reqs = ProjectComponent.query.filter_by(project_id=dustbin_id).all()
        total_required_units = sum(r.required_quantity for r in reqs)
        assert total_required_units == 4, f"Expected 4 required units, got {total_required_units}"

        # Find or ensure marketplace components exist for requirements
        comp_uno = Component.query.filter_by(name='Arduino Uno').first()
        comp_us = Component.query.filter_by(name='Ultrasonic Sensor').first()
        comp_servo = Component.query.filter_by(name='Servo Motor').first()
        comp_wires = Component.query.filter_by(name='Jumper Wires').first()

        assert comp_uno and comp_us and comp_servo and comp_wires, "Required marketplace components missing"

        # Ensure marketplace store has stock for testing
        uno_id = comp_uno.id
        us_id = comp_us.id
        servo_id = comp_servo.id
        wires_id = comp_wires.id

        orig_uno_stock = comp_uno.quantity
        orig_us_stock = comp_us.quantity
        orig_servo_stock = comp_servo.quantity
        orig_wires_stock = comp_wires.quantity

        comp_uno.quantity = max(comp_uno.quantity, 10)
        comp_us.quantity = max(comp_us.quantity, 10)
        comp_servo.quantity = max(comp_servo.quantity, 10)
        comp_wires.quantity = max(comp_wires.quantity, 10)
        db.session.commit()

    with app.test_client() as client:
        try:
            # ─────────────────────────────────────────────────────────────
            # Test 1: New user owns nothing. Expected feasibility = 0%.
            # ─────────────────────────────────────────────────────────────
            print("\n[Test 1] New User Owns Nothing")
            res = client.post('/register', data={
                'name': 'Buyer One',
                'email': 'inv_buyer1@example.com',
                'password': 'password123',
                'confirm_password': 'password123'
            }, follow_redirects=True)
            assert res.status_code == 200

            client.post('/login', data={
                'email': 'inv_buyer1@example.com',
                'password': 'password123'
            }, follow_redirects=True)

            with app.app_context():
                user1 = User.query.filter_by(email='inv_buyer1@example.com').first()
                user1_id = user1.id
                match1 = find_matching_components(user1_id, dustbin_id)
                assert match1 is not None
                assert match1['feasibility_score'] == 0.0, f"Expected 0%, got {match1['feasibility_score']}%"
                assert match1['total_satisfied'] == 0
                assert match1['total_required'] == 4
                assert len(match1['matched']) == 0
                assert len(match1['missing']) == 4
                print("  [OK] New user feasibility = 0.0% with 0/4 satisfied parts")

            # ─────────────────────────────────────────────────────────────
            # Test 2: Buy one required component. Feasibility increases according to formula.
            # ─────────────────────────────────────────────────────────────
            print("\n[Test 2] Buy One Required Component (Arduino Uno)")
            # Add Arduino Uno to cart
            res = client.post(f'/cart/add/{uno_id}', data={'quantity': 1}, follow_redirects=True)
            assert res.status_code == 200

            # Checkout via Razorpay verify flow
            res = client.post('/checkout/razorpay/verify', json={
                'razorpay_order_id': 'order_demo_test1_uno',
                'razorpay_payment_id': 'pay_demo_test1_uno',
                'razorpay_signature': 'demo_sig_test1',
                'customer_name': 'Buyer One',
                'email': 'inv_buyer1@example.com',
                'phone': '9876543210',
                'address': '123 Test Street',
                'city': 'Bengaluru',
                'state': 'Karnataka',
                'pincode': '560001'
            })
            assert res.status_code == 200
            data = res.get_json()
            assert data.get('success') is True, f"Checkout failed: {data}"

            with app.app_context():
                # Check user owns 1 Arduino Uno in user_components
                uc = UserComponent.query.filter_by(user_id=user1_id, component_id=uno_id).first()
                assert uc is not None, "UserComponent record not created after purchase"
                assert uc.quantity == 1, f"Expected 1 owned Arduino Uno, got {uc.quantity}"

                match2 = find_matching_components(user1_id, dustbin_id)
                # Formula: 1 / 4 * 100 = 25.0%
                expected_score = round(1 / 4 * 100, 1)
                assert match2['feasibility_score'] == expected_score, f"Expected {expected_score}%, got {match2['feasibility_score']}%"
                assert match2['total_satisfied'] == 1
                assert len(match2['matched']) == 1
                assert match2['matched'][0]['name'] == 'Arduino Uno'
                print(f"  [OK] Purchased Arduino Uno. Feasibility increased to {match2['feasibility_score']}% (1/4)")

            # ─────────────────────────────────────────────────────────────
            # Test 3: Buy all required components. Expected feasibility = 100%.
            # ─────────────────────────────────────────────────────────────
            print("\n[Test 3] Buy All Remaining Required Components")
            # Buy Ultrasonic Sensor, Servo Motor, Jumper Wires
            for cid in [us_id, servo_id, wires_id]:
                client.post(f'/cart/add/{cid}', data={'quantity': 1}, follow_redirects=True)

            res = client.post('/checkout/razorpay/verify', json={
                'razorpay_order_id': 'order_demo_test3_all',
                'razorpay_payment_id': 'pay_demo_test3_all',
                'razorpay_signature': 'demo_sig_test3',
                'customer_name': 'Buyer One',
                'email': 'inv_buyer1@example.com',
                'phone': '9876543210',
                'address': '123 Test Street',
                'city': 'Bengaluru',
                'state': 'Karnataka',
                'pincode': '560001'
            })
            assert res.status_code == 200
            assert res.get_json().get('success') is True

            with app.app_context():
                match3 = find_matching_components(user1_id, dustbin_id)
                assert match3['feasibility_score'] == 100.0, f"Expected 100%, got {match3['feasibility_score']}%"
                assert match3['total_satisfied'] == 4
                assert len(match3['missing']) == 0
                assert len(match3['matched']) == 4
                print("  [OK] Purchased all parts. Feasibility = 100.0% (4/4 satisfied, 0 missing)")

            # ─────────────────────────────────────────────────────────────
            # Test 4: Buy 2 units of a component requiring 1.
            # Expected requirement is satisfied without producing an incorrect percentage.
            # ─────────────────────────────────────────────────────────────
            print("\n[Test 4] Buy 2 Units of Component Requiring 1")
            client.post(f'/cart/add/{uno_id}', data={'quantity': 1}, follow_redirects=True)
            res = client.post('/checkout/razorpay/verify', json={
                'razorpay_order_id': 'order_demo_test4_extra',
                'razorpay_payment_id': 'pay_demo_test4_extra',
                'razorpay_signature': 'demo_sig_test4',
                'customer_name': 'Buyer One',
                'email': 'inv_buyer1@example.com',
                'phone': '9876543210',
                'address': '123 Test Street',
                'city': 'Bengaluru',
                'state': 'Karnataka',
                'pincode': '560001'
            })
            assert res.status_code == 200
            assert res.get_json().get('success') is True

            with app.app_context():
                uc_uno = UserComponent.query.filter_by(user_id=user1_id, component_id=uno_id).first()
                assert uc_uno.quantity == 2, f"Expected 2 owned Arduino Unos, got {uc_uno.quantity}"

                match4 = find_matching_components(user1_id, dustbin_id)
                # Requirement is 1, satisfied must cap at 1. Total satisfied must be 4 / 4 * 100 = 100%
                assert match4['feasibility_score'] == 100.0, f"Expected 100%, got {match4['feasibility_score']}%"
                assert match4['total_satisfied'] == 4, f"Expected 4 satisfied units, got {match4['total_satisfied']}"
                print("  [OK] User owns 2 Arduino Unos for requirement of 1. Score capped correctly at 100.0%")

            # ─────────────────────────────────────────────────────────────
            # Test 5: Another user owns the component. Current user must still show 0%.
            # ─────────────────────────────────────────────────────────────
            print("\n[Test 5] Cross-User Inventory Isolation")
            client.get('/logout')

            # Register User Two
            res = client.post('/register', data={
                'name': 'Buyer Two',
                'email': 'inv_buyer2@example.com',
                'password': 'password123',
                'confirm_password': 'password123'
            }, follow_redirects=True)
            assert res.status_code == 200

            client.post('/login', data={
                'email': 'inv_buyer2@example.com',
                'password': 'password123'
            }, follow_redirects=True)

            with app.app_context():
                user2 = User.query.filter_by(email='inv_buyer2@example.com').first()
                user2_id = user2.id
                # User 2 owns nothing; User 1 owns components
                match5 = find_matching_components(user2_id, dustbin_id)
                assert match5['feasibility_score'] == 0.0, f"Expected User 2 to have 0%, got {match5['feasibility_score']}%"
                assert match5['total_satisfied'] == 0
                print("  [OK] User 2 shows 0.0% feasibility despite User 1 and store having stock")

            # ─────────────────────────────────────────────────────────────
            # Test 6: Complete the project. Required components consumed from inventory.
            # ─────────────────────────────────────────────────────────────
            print("\n[Test 6] Complete Project & Component Consumption")
            # Log back in as User 1
            client.get('/logout')
            client.post('/login', data={
                'email': 'inv_buyer1@example.com',
                'password': 'password123'
            }, follow_redirects=True)

            # Complete project Smart Dustbin
            res = client.post(f'/projects/{dustbin_id}/complete', follow_redirects=True)
            assert res.status_code == 200
            assert b"completed" in res.data

            with app.app_context():
                # Check ReuseHistory created
                history = ReuseHistory.query.filter_by(user_id=user1_id, project_id=dustbin_id).all()
                assert len(history) > 0, "Expected ReuseHistory records to be created"
                total_diverted = sum(h.waste_reduced for h in history)
                assert total_diverted > 0, f"Expected positive diverted waste, got {total_diverted}"

                # Check inventory consumption:
                # Uno: was 2, consumed 1 -> now 1
                # US: was 1, consumed 1 -> now 0
                # Servo: was 1, consumed 1 -> now 0
                # Wires: was 1, consumed 1 -> now 0
                uc_uno = UserComponent.query.filter_by(user_id=user1_id, component_id=uno_id).first()
                uc_us = UserComponent.query.filter_by(user_id=user1_id, component_id=us_id).first()
                uc_servo = UserComponent.query.filter_by(user_id=user1_id, component_id=servo_id).first()
                uc_wires = UserComponent.query.filter_by(user_id=user1_id, component_id=wires_id).first()

                assert uc_uno.quantity == 1, f"Expected Uno qty 1, got {uc_uno.quantity}"
                assert uc_us.quantity == 0, f"Expected US qty 0, got {uc_us.quantity}"
                assert uc_servo.quantity == 0, f"Expected Servo qty 0, got {uc_servo.quantity}"
                assert uc_wires.quantity == 0, f"Expected Wires qty 0, got {uc_wires.quantity}"

                # None of the quantities are negative
                for c_item in [uc_uno, uc_us, uc_servo, uc_wires]:
                    assert c_item.quantity >= 0, f"Negative quantity found: {c_item}"

                # Feasibility recalculates to 1 / 4 * 100 = 25.0%
                match6 = find_matching_components(user1_id, dustbin_id)
                assert match6['feasibility_score'] == 25.0, f"Expected 25.0%, got {match6['feasibility_score']}%"
                print(f"  [OK] Project completed! {total_diverted}g diverted. Inventory consumed without negatives.")
                print(f"  [OK] Recalculated feasibility: {match6['feasibility_score']}% (1 remaining Arduino Uno)")

            # ─────────────────────────────────────────────────────────────
            # Test 7: Refresh / re-login. Inventory & feasibility remain correct.
            # ─────────────────────────────────────────────────────────────
            print("\n[Test 7] Refresh / Re-login Persistence")
            client.get('/logout')
            res = client.post('/login', data={
                'email': 'inv_buyer1@example.com',
                'password': 'password123'
            }, follow_redirects=True)
            assert res.status_code == 200

            # Verify /my-inventory page
            res = client.get('/my-inventory')
            assert res.status_code == 200
            assert b"Arduino Uno" in res.data
            print("  [OK] /my-inventory displays persisted Arduino Uno (1 unit)")

            # Verify project detail page
            res = client.get(f'/projects/{dustbin_id}')
            assert res.status_code == 200
            assert b"25.0%" in res.data or b"25%" in res.data
            assert b"Available" in res.data
            assert b"Missing" in res.data
            assert b"Completed" in res.data
            print("  [OK] Project details accurately display persisted 25.0% feasibility and Available/Missing lists")

        finally:
            # Clean up test users and restore store stock
            with app.app_context():
                for email in ['inv_buyer1@example.com', 'inv_buyer2@example.com']:
                    u = User.query.filter_by(email=email).first()
                    if u:
                        CartItem.query.filter_by(user_id=u.id).delete()
                        orders = Order.query.filter_by(user_id=u.id).all()
                        for o in orders:
                            OrderItem.query.filter_by(order_id=o.id).delete()
                            db.session.delete(o)
                        UserComponent.query.filter_by(user_id=u.id).delete()
                        ReuseHistory.query.filter_by(user_id=u.id).delete()
                        db.session.delete(u)

                # Restore component stock
                c1 = Component.query.get(uno_id)
                c2 = Component.query.get(us_id)
                c3 = Component.query.get(servo_id)
                c4 = Component.query.get(wires_id)
                if c1: c1.quantity = orig_uno_stock
                if c2: c2.quantity = orig_us_stock
                if c3: c3.quantity = orig_servo_stock
                if c4: c4.quantity = orig_wires_stock
                db.session.commit()
                print("\n[Teardown] Test users and temporary stock cleaned up.")

    print("\n" + "=" * 70)
    print("ALL 7 INVENTORY & MATCHING ENGINE INTEGRATION TESTS PASSED (100%)!")
    print("=" * 70)


if __name__ == '__main__':
    run_inventory_matching_tests()
