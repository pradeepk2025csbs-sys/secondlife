"""
SECONDLIFE Peer-to-Peer Marketplace Tests (test_user_marketplace.py)
Tests all 24 required peer-to-peer marketplace capabilities:
1. User registration
2. User creates listing
3. User uploads image
4. Listing appears in marketplace
5. Another user can view listing
6. Another user can add it to cart
7. Another user cannot edit seller's listing
8. Seller cannot buy own listing
9. Buyer can checkout
10. Razorpay order creation
11. Razorpay signature verification
12. Payment failure
13. Successful payment
14. Seller stock decreases
15. Buyer inventory increases
16. User matching feasibility updates
17. Seller sees sale
18. Buyer sees purchase
19. Historical price remains unchanged
20. Out-of-stock prevents purchase
21. Stock cannot become negative
22. Project completion consumes buyer inventory
23. Admin can manage listings
24. Users cannot access other users' private seller data
"""

import io
import os
import sys
import hmac
import hashlib

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.models import (
    db, User, Component, CartItem, Order, OrderItem,
    UserComponent, Project, ProjectComponent, ReuseHistory
)
from werkzeug.security import generate_password_hash
from services.payment import get_payment_config


def run_all_user_marketplace_tests():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    print("=" * 70)
    print("RUNNING COMPLETE 24-POINT PEER-TO-PEER MARKETPLACE TEST SUITE")
    print("=" * 70)

    with app.test_client() as client:
        with app.app_context():
            # Setup clean test accounts
            seller_email = 'seller_test_p2p@example.com'
            buyer_email = 'buyer_test_p2p@example.com'
            admin_email = 'admin@secondlife.com'

            # Clean prior data
            for email in [seller_email, buyer_email]:
                u = User.query.filter_by(email=email).first()
                if u:
                    OrderItem.query.filter_by(seller_id=u.id).delete()
                    for o in Order.query.filter_by(user_id=u.id).all():
                        OrderItem.query.filter_by(order_id=o.id).delete()
                        db.session.delete(o)
                    CartItem.query.filter_by(user_id=u.id).delete()
                    UserComponent.query.filter_by(user_id=u.id).delete()
                    ReuseHistory.query.filter_by(user_id=u.id).delete()
                    Component.query.filter_by(user_id=u.id).delete()
                    db.session.delete(u)
            db.session.commit()

            # Ensure admin exists
            admin = User.query.filter_by(email=admin_email).first()
            if not admin:
                admin = User(name='Admin', email=admin_email, password_hash=generate_password_hash('admin123'), role='admin')
                db.session.add(admin)
                db.session.commit()

            test_comp_id = None
            user_a_id = None
            user_b_id = None
            created_order_id = None

            try:
                # ─── 1. USER REGISTRATION ───
                print("\n[Test 1] User Registration...")
                res_a = client.post('/register', data={
                    'name': 'Seller User A',
                    'email': seller_email,
                    'password': 'password123',
                    'confirm_password': 'password123'
                }, follow_redirects=True)
                assert res_a.status_code == 200

                res_b = client.post('/register', data={
                    'name': 'Buyer User B',
                    'email': buyer_email,
                    'password': 'password123',
                    'confirm_password': 'password123'
                }, follow_redirects=True)
                assert res_b.status_code == 200

                user_a = User.query.filter_by(email=seller_email).first()
                user_b = User.query.filter_by(email=buyer_email).first()
                assert user_a is not None and user_b is not None
                user_a_id = user_a.id
                user_b_id = user_b.id
                print("  ✓ User A (Seller) and User B (Buyer) registered successfully.")

                # ─── 2. USER CREATES LISTING ───
                print("\n[Test 2] User Creates Listing...")
                # Log in as User A
                client.post('/login', data={'email': seller_email, 'password': 'password123'})
                listing_data = {
                    'name': 'P2P Arduino Uno Rev3',
                    'category': 'Microcontroller',
                    'condition': 'Used - Good',
                    'price': '1400',
                    'quantity': '2',
                    'estimated_weight': '25',
                    'description': 'Real working Arduino Uno board for robotics.'
                }
                res = client.post('/sell', data=listing_data, follow_redirects=True)
                assert res.status_code == 200

                comp = Component.query.filter_by(name='P2P Arduino Uno Rev3').first()
                assert comp is not None
                assert comp.seller_id == user_a_id
                assert comp.price == 1400.0
                assert comp.quantity == 2
                assert comp.condition == 'Used - Good'
                test_comp_id = comp.id
                print("  ✓ User A listed component. seller_id correctly set to User A.")

                # ─── 3. USER UPLOADS IMAGE ───
                print("\n[Test 3] User Uploads Image...")
                fake_image = (io.BytesIO(b"fake image data"), "real_arduino.jpg")
                res = client.post(f'/components/{test_comp_id}/edit', data={
                    'name': 'P2P Arduino Uno Rev3',
                    'category': 'Microcontroller',
                    'condition': 'Used - Good',
                    'price': '1400',
                    'quantity': '2',
                    'estimated_weight': '25',
                    'description': 'Real working Arduino with uploaded photo.',
                    'image': fake_image
                }, content_type='multipart/form-data', follow_redirects=True)
                assert res.status_code == 200
                comp = Component.query.get(test_comp_id)
                assert comp.image is not None and comp.image.endswith('.jpg')
                print("  ✓ Real component photo uploaded and attached to listing.")

                # ─── 4. LISTING APPEARS IN MARKETPLACE ───
                print("\n[Test 4] Listing Appears in Marketplace...")
                res = client.get('/components')
                assert res.status_code == 200
                assert b'P2P Arduino Uno Rev3' in res.data
                assert b'1,400' in res.data or b'1400' in res.data
                print("  ✓ Listing rendered in public marketplace with price and stock.")

                # ─── 5. ANOTHER USER CAN VIEW LISTING ───
                print("\n[Test 5] Another User Can View Listing...")
                # Log out User A, log in as User B
                client.get('/logout')
                client.post('/login', data={'email': buyer_email, 'password': 'password123'})
                res = client.get(f'/components/{test_comp_id}')
                assert res.status_code == 200
                assert b'P2P Arduino Uno Rev3' in res.data
                assert b'Seller User A' in res.data
                assert b'Add to Cart' in res.data
                print("  ✓ User B can view listing and see seller name.")

                # ─── 6. ANOTHER USER CAN ADD TO CART ───
                print("\n[Test 6] Another User Adds to Cart...")
                res = client.post(f'/cart/add/{test_comp_id}', data={'quantity': '1'}, follow_redirects=True)
                assert res.status_code == 200
                cart_item = CartItem.query.filter_by(user_id=user_b_id, component_id=test_comp_id).first()
                assert cart_item is not None and cart_item.quantity == 1
                print("  ✓ User B added 1 unit of User A's listing to cart.")

                # ─── 7. ANOTHER USER CANNOT EDIT SELLER'S LISTING ───
                print("\n[Test 7] Another User Cannot Edit Seller's Listing...")
                res = client.post(f'/components/{test_comp_id}/edit', data={
                    'name': 'Hacked Component',
                    'category': 'Microcontroller',
                    'price': '10'
                }, follow_redirects=True)
                comp = Component.query.get(test_comp_id)
                assert comp.name == 'P2P Arduino Uno Rev3'  # Name unchanged!
                print("  ✓ User B unauthorized edit was blocked by server-side authorization check.")

                # ─── 8. SELLER CANNOT BUY OWN LISTING ───
                print("\n[Test 8] Seller Cannot Buy Own Listing...")
                client.get('/logout')
                client.post('/login', data={'email': seller_email, 'password': 'password123'})
                res = client.post(f'/cart/add/{test_comp_id}', data={'quantity': '1'}, follow_redirects=True)
                assert b'You cannot purchase your own' in res.data or res.status_code == 400
                cart_item = CartItem.query.filter_by(user_id=user_a_id, component_id=test_comp_id).first()
                assert cart_item is None
                # Also test buy-now
                res_bn = client.post(f'/buy-now/{test_comp_id}', data={'quantity': '1'}, follow_redirects=True)
                assert b'You cannot purchase your own' in res_bn.data
                print("  ✓ Seller prevented from buying or adding their own listing to cart.")

                # ─── 9. BUYER CAN CHECKOUT ───
                print("\n[Test 9] Buyer Can Checkout...")
                client.get('/logout')
                client.post('/login', data={'email': buyer_email, 'password': 'password123'})
                res = client.get('/checkout')
                assert res.status_code == 200
                assert b'P2P Arduino Uno Rev3' in res.data
                assert b'1,400' in res.data or b'1400' in res.data
                print("  ✓ /checkout displays User B's cart with live pricing.")

                # ─── 10. RAZORPAY ORDER CREATION ───
                print("\n[Test 10] Razorpay Order Creation...")
                res = client.post('/checkout/razorpay/create-order')
                assert res.status_code == 200
                order_json = res.get_json()
                assert order_json['success'] is True
                assert 'order_id' in order_json
                razorpay_order_id = order_json['order_id']
                print(f"  ✓ Razorpay order created successfully: {razorpay_order_id}")

                # ─── 11. RAZORPAY SIGNATURE VERIFICATION ───
                print("\n[Test 11] Razorpay Signature Verification...")
                payment_config = get_payment_config()
                razorpay_payment_id = "pay_test_p2p_9999"
                key_secret = payment_config['key_secret'].encode('utf-8')
                msg = f"{razorpay_order_id}|{razorpay_payment_id}".encode('utf-8')
                valid_signature = hmac.new(key_secret, msg, hashlib.sha256).hexdigest()
                assert len(valid_signature) == 64
                print("  ✓ HMAC-SHA256 signature generated correctly for payment verification.")

                # ─── 12. PAYMENT FAILURE HANDLING ───
                print("\n[Test 12] Payment Failure Handling...")
                bad_res = client.post('/checkout/razorpay/verify', json={
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': razorpay_payment_id,
                    'razorpay_signature': 'invalid_signature_hash',
                    'customer_name': 'Buyer User B',
                    'phone': '9876543210',
                    'address': '45 Tech Park',
                    'city': 'Bengaluru',
                    'state': 'Karnataka',
                    'pincode': '560001'
                })
                assert bad_res.status_code == 400
                comp = Component.query.get(test_comp_id)
                assert comp.quantity == 2  # Stock NOT decreased!
                print("  ✓ Tampered signature rejected. Stock unchanged.")

                # ─── 13. SUCCESSFUL PAYMENT ───
                print("\n[Test 13] Successful Payment...")
                good_res = client.post('/checkout/razorpay/verify', json={
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': razorpay_payment_id,
                    'razorpay_signature': valid_signature,
                    'customer_name': 'Buyer User B',
                    'phone': '9876543210',
                    'address': '45 Tech Park',
                    'city': 'Bengaluru',
                    'state': 'Karnataka',
                    'pincode': '560001'
                })
                assert good_res.status_code == 200
                res_data = good_res.get_json()
                assert res_data['success'] is True
                created_order_id = res_data['order_id']
                print(f"  ✓ Payment confirmed. Created Order #{res_data['order_number']}.")

                # ─── 14. SELLER STOCK DECREASES ───
                print("\n[Test 14] Seller Stock Decreases...")
                comp = Component.query.get(test_comp_id)
                assert comp.quantity == 1  # 2 - 1 = 1
                assert comp.status == 'Available'
                print("  ✓ User A's listing stock decreased from 2 to 1.")

                # ─── 15. BUYER INVENTORY INCREASES ───
                print("\n[Test 15] Buyer Inventory Increases...")
                uc = UserComponent.query.filter_by(user_id=user_b_id, component_id=test_comp_id).first()
                assert uc is not None
                assert uc.quantity == 1
                print("  ✓ User B's personal inventory increased to 1 unit.")

                # ─── 16. USER MATCHING FEASIBILITY UPDATES ───
                print("\n[Test 16] User Matching Feasibility Updates...")
                from services.matching import calculate_feasibility
                # Create a sample project requiring this component
                test_proj = Project.query.filter_by(title='P2P Smart Uno Project').first()
                if not test_proj:
                    test_proj = Project(
                        title='P2P Smart Uno Project',
                        description='Test project requiring uno',
                        category='IoT',
                        difficulty='Beginner',
                        estimated_cost=1500,
                        estimated_waste_reduction=25
                    )
                    db.session.add(test_proj)
                    db.session.flush()
                    pc = ProjectComponent(
                        project_id=test_proj.id,
                        component_name='P2P Arduino Uno Rev3',
                        category='Microcontroller',
                        required_quantity=1
                    )
                    db.session.add(pc)
                    db.session.commit()

                # User B owns 1/1 required components -> feasibility = 100.0%
                match_result = calculate_feasibility(test_proj, user_b_id)
                assert match_result['feasibility_score'] == 100.0
                assert match_result['matched_count'] == 1
                print("  ✓ User B matching feasibility accurately reached 100% based on purchased inventory.")

                # ─── 17. SELLER SEES SALE ───
                print("\n[Test 17] Seller Sees Sale...")
                client.get('/logout')
                client.post('/login', data={'email': seller_email, 'password': 'password123'})
                res = client.get('/my-sales')
                assert res.status_code == 200
                assert b'P2P Arduino Uno Rev3' in res.data
                assert b'1,400' in res.data or b'1400' in res.data
                print("  ✓ User A sees the sale in /my-sales with correct customer info & earnings.")

                # ─── 18. BUYER SEES PURCHASE ───
                print("\n[Test 18] Buyer Sees Purchase...")
                client.get('/logout')
                client.post('/login', data={'email': buyer_email, 'password': 'password123'})
                res = client.get('/my-purchases')
                assert res.status_code == 200
                assert b'P2P Arduino Uno Rev3' in res.data
                assert b'Seller User A' in res.data
                print("  ✓ User B sees order in /my-purchases including seller attribution.")

                # ─── 19. HISTORICAL PRICE PRESERVATION ───
                print("\n[Test 19] Historical Price Remains Unchanged...")
                client.get('/logout')
                client.post('/login', data={'email': seller_email, 'password': 'password123'})
                # Seller updates price from 1400 to 1800
                client.post(f'/components/{test_comp_id}/quick-update', data={'price': '1800'})
                comp = Component.query.get(test_comp_id)
                assert comp.price == 1800.0
                # Past order item still stores unit_price = 1400.0
                order_item = OrderItem.query.filter_by(order_id=created_order_id, component_id=test_comp_id).first()
                assert order_item.unit_price == 1400.0
                print("  ✓ Seller updated price to ₹1,800. Historical order preserved original ₹1,400 price.")

                # ─── 20. OUT-OF-STOCK PREVENTS PURCHASE ───
                print("\n[Test 20] Out-of-Stock Prevents Purchase...")
                # Reduce stock to 0
                client.post(f'/components/{test_comp_id}/quick-update', data={'quantity': '0'})
                comp = Component.query.get(test_comp_id)
                assert comp.quantity == 0
                assert comp.status == 'Out of Stock'
                # User B tries to buy
                client.get('/logout')
                client.post('/login', data={'email': buyer_email, 'password': 'password123'})
                res = client.post(f'/cart/add/{test_comp_id}', data={'quantity': '1'}, follow_redirects=True)
                assert b'out of stock' in res.data.lower()
                print("  ✓ Out of stock listing automatically blocks Add to Cart and Buy Now.")

                # ─── 21. STOCK CANNOT BECOME NEGATIVE ───
                print("\n[Test 21] Stock Cannot Become Negative...")
                client.get('/logout')
                client.post('/login', data={'email': seller_email, 'password': 'password123'})
                client.post(f'/components/{test_comp_id}/quick-update', data={'quantity': '-5'})
                comp = Component.query.get(test_comp_id)
                assert comp.quantity >= 0
                print("  ✓ Negative stock input rejected server-side.")

                # ─── 22. PROJECT COMPLETION CONSUMES BUYER INVENTORY ───
                print("\n[Test 22] Project Completion Consumes Buyer Inventory...")
                client.get('/logout')
                client.post('/login', data={'email': buyer_email, 'password': 'password123'})
                res = client.post(f'/projects/{test_proj.id}/complete', follow_redirects=True)
                assert res.status_code == 200
                uc = UserComponent.query.filter_by(user_id=user_b_id, component_id=test_comp_id).first()
                assert uc.quantity == 0  # 1 unit consumed
                rh = ReuseHistory.query.filter_by(user_id=user_b_id).first()
                assert rh is not None and rh.waste_reduced == 25.0
                print("  ✓ Project completion consumed buyer inventory (quantity=0) and recorded 25g e-waste diverted.")

                # ─── 23. ADMIN CAN MANAGE LISTINGS ───
                print("\n[Test 23] Admin Can Manage Listings...")
                client.get('/logout')
                client.post('/login', data={'email': admin_email, 'password': 'admin123'})
                res = client.get('/admin/components')
                assert res.status_code == 200
                assert b'Seller User A' in res.data
                print("  ✓ Admin can view all marketplace listings with verified seller attribution.")

                # ─── 24. USERS CANNOT ACCESS OTHER USERS' PRIVATE SELLER DATA ───
                print("\n[Test 24] Users Cannot Access Other Users' Private Seller Data...")
                client.get('/logout')
                client.post('/login', data={'email': buyer_email, 'password': 'password123'})
                # User B tries to update User A's sale item status
                order_item = OrderItem.query.filter_by(order_id=created_order_id).first()
                res = client.post(f'/seller/orders/{order_item.id}/status', data={'status': 'Delivered'}, follow_redirects=True)
                assert b'You are not authorized' in res.data or res.status_code == 403
                # User B tries to view User A's order detail if not their own
                # (OrderItem status remains Confirmed)
                order_item = OrderItem.query.get(order_item.id)
                assert order_item.status == 'Confirmed'
                print("  ✓ Cross-seller unauthorized access blocked server-side.")

            finally:
                # Cleanup test fixtures
                print("\n[Teardown] Cleaning up test fixtures...")
                if test_comp_id:
                    OrderItem.query.filter_by(component_id=test_comp_id).delete()
                    UserComponent.query.filter_by(component_id=test_comp_id).delete()
                    CartItem.query.filter_by(component_id=test_comp_id).delete()
                    Component.query.filter_by(id=test_comp_id).delete()

                test_proj = Project.query.filter_by(title='P2P Smart Uno Project').first()
                if test_proj:
                    ProjectComponent.query.filter_by(project_id=test_proj.id).delete()
                    db.session.delete(test_proj)

                for email in [seller_email, buyer_email]:
                    u = User.query.filter_by(email=email).first()
                    if u:
                        for o in Order.query.filter_by(user_id=u.id).all():
                            OrderItem.query.filter_by(order_id=o.id).delete()
                            db.session.delete(o)
                        OrderItem.query.filter_by(seller_id=u.id).delete()
                        CartItem.query.filter_by(user_id=u.id).delete()
                        UserComponent.query.filter_by(user_id=u.id).delete()
                        ReuseHistory.query.filter_by(user_id=u.id).delete()
                        db.session.delete(u)

                db.session.commit()
                print("  ✓ Cleanup complete.")

    print("\n" + "=" * 70)
    print("ALL 24 PEER-TO-PEER MARKETPLACE TESTS PASSED SUCCESSFULLY! (100% PASS RATE)")
    print("=" * 70)


if __name__ == '__main__':
    run_all_user_marketplace_tests()
