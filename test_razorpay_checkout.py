"""
SECONDLIFE – Automated Test Suite for Razorpay Payment Integration & Component Pricing
Tests:
1. Payment service unit tests (order creation, signature verification, commission calculation)
2. Razorpay create-order API endpoint (/checkout/razorpay/create-order)
3. Razorpay verify API endpoint (/checkout/razorpay/verify)
4. Stock reduction, cart clearance, and transaction persistence
5. Order detail view rendering with payment badges
6. Admin orders list & order detail view with payment info
7. Add & Edit component pricing inputs
"""

import sys
import unittest
from app import create_app
from models.models import db, User, Component, CartItem, Order, OrderItem
from services.payment import (
    create_payment_order,
    verify_payment_signature,
    is_demo_mode,
    calculate_platform_fees
)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


class RazorpayIntegrationTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

        with self.app.app_context():
            # Find or create a test user
            self.user = User.query.filter_by(email='rahul@example.com').first()
            if not self.user:
                self.user = User(
                    name='Test Maker Rahul',
                    email='rahul@example.com',
                    role='maker'
                )
                self.user.set_password('password123')
                db.session.add(self.user)
                db.session.commit()
            self.user_id = self.user.id
            self.user_name = self.user.name
            self.user_role = self.user.role

            # Find or create admin user
            self.admin = User.query.filter_by(email='admin@secondlife.com').first()
            if not self.admin:
                self.admin = User(
                    name='Admin System',
                    email='admin@secondlife.com',
                    role='admin'
                )
                self.admin.set_password('admin123')
                db.session.add(self.admin)
                db.session.commit()
            self.admin_id = self.admin.id
            self.admin_name = self.admin.name

            # Pre-clean any leftover test components / orders from any previous interrupted run
            old_orders = Order.query.filter(Order.customer_name.like('%Razorpay Test%')).all()
            for o in old_orders:
                db.session.delete(o)
            old_comps = Component.query.filter(Component.name.like('%Razorpay Test%')).all()
            for c in old_comps:
                db.session.delete(c)
            db.session.commit()

            # Create a dedicated test component
            self.test_comp = Component(
                user_id=self.user_id,
                name='Razorpay Test Microcontroller ESP32',
                category='Microcontrollers',
                quantity=10,
                price=350.0,
                condition='Good',
                estimated_weight=20.0,
                status='Available'
            )
            db.session.add(self.test_comp)
            db.session.commit()
            self.comp_id = self.test_comp.id
            self.comp_price = self.test_comp.price

    def tearDown(self):
        with self.app.app_context():
            # Clean up test orders and items
            orders = Order.query.filter(Order.customer_name.like('%Razorpay Test%')).all()
            for o in orders:
                db.session.delete(o)

            # Clean up cart items for user
            CartItem.query.filter_by(user_id=self.user_id).delete()

            # Clean up test component
            comp = Component.query.get(self.comp_id)
            if comp:
                db.session.delete(comp)

            db.session.commit()

    def login_user(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.user_id
            sess['user_name'] = self.user_name
            sess['user_role'] = self.user_role

    def login_admin(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.admin_id
            sess['user_name'] = self.admin_name
            sess['user_role'] = 'admin'

    # ─── 1. Payment Service Unit Tests ───

    def test_01_payment_service_order_creation(self):
        print("\n[Test 1] Payment Service Order Creation & Currency Units")
        order_data = create_payment_order(amount_inr=350.0, receipt="test_rcpt_101")
        self.assertIn('id', order_data)
        self.assertEqual(order_data['amount'], 35000)  # 350 * 100 paise
        self.assertEqual(order_data['currency'], 'INR')
        self.assertEqual(order_data['status'], 'created')
        print(f"  [OK] Order created with ID: {order_data['id']}, amount: {order_data['amount']} paise")

    def test_02_payment_signature_verification(self):
        print("\n[Test 2] Payment Signature Verification & Rejection")
        # In demo mode, simulated order/signature verifies
        valid, msg = verify_payment_signature("order_demo_12345", "pay_demo_67890", "demo_sig_abcde")
        self.assertTrue(valid)
        print(f"  [OK] Valid demo signature passed: {msg}")

        # Missing order ID should fail
        invalid, err = verify_payment_signature("", "pay_demo_67890", "demo_sig_abcde")
        self.assertFalse(invalid)
        print(f"  [OK] Empty order ID properly rejected: {err}")

    def test_03_fee_calculation(self):
        print("\n[Test 3] Marketplace Platform Fee Calculation")
        fees = calculate_platform_fees(total_amount=1000.0)
        self.assertEqual(fees['total_amount'], 1000.0)
        self.assertEqual(fees['commission_pct'], 5.0)
        self.assertEqual(fees['platform_fee'], 50.0)
        self.assertEqual(fees['seller_amount'], 950.0)
        print(f"  [OK] 5% fee on ₹1000 = ₹{fees['platform_fee']}, seller payout = ₹{fees['seller_amount']}")

    # ─── 2. Route Endpoints Tests ───

    def test_04_create_order_empty_cart_rejection(self):
        print("\n[Test 4] Reject Order Creation on Empty Cart")
        self.login_user()
        res = self.client.post('/checkout/razorpay/create-order')
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data['success'])
        self.assertIn('empty', data['error'].lower())
        print("  [OK] Empty cart prevented from generating Razorpay order")

    def test_05_create_order_with_cart_items(self):
        print("\n[Test 5] Create Razorpay Order with Active Cart")
        self.login_user()
        # Add 2 units of test component (2 x ₹350 = ₹700)
        with self.app.app_context():
            cart_item = CartItem(user_id=self.user_id, component_id=self.comp_id, quantity=2)
            db.session.add(cart_item)
            db.session.commit()

        res = self.client.post('/checkout/razorpay/create-order')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['amount'], 70000)  # ₹700.00 -> 70000 paise
        self.assertEqual(data['currency'], 'INR')
        self.assertTrue(data['order_id'].startswith('order_'))
        print(f"  [OK] Order successfully created: {data['order_id']} for ₹{data['amount_inr']}")

    def test_06_razorpay_verify_and_order_persistence(self):
        print("\n[Test 6] Razorpay Verification, Order Persistence & Inventory Decrement")
        self.login_user()

        with self.app.app_context():
            # Add 3 units of test component (3 x ₹350 = ₹1050)
            cart_item = CartItem(user_id=self.user_id, component_id=self.comp_id, quantity=3)
            db.session.add(cart_item)
            db.session.commit()

        # Step 1: Create order
        create_res = self.client.post('/checkout/razorpay/create-order')
        order_info = create_res.get_json()
        rzp_order_id = order_info['order_id']

        # Step 2: Verify payment
        payload = {
            'razorpay_order_id': rzp_order_id,
            'razorpay_payment_id': 'pay_demo_test_9988',
            'razorpay_signature': 'demo_sig_verified_123',
            'customer_name': 'Razorpay Test Buyer',
            'email': 'buyer@example.com',
            'phone': '9876543210',
            'address': '123 Maker Street, Tech Hub',
            'city': 'Bengaluru',
            'state': 'Karnataka',
            'pincode': '560001'
        }

        verify_res = self.client.post('/checkout/razorpay/verify', json=payload)
        self.assertEqual(verify_res.status_code, 200)
        v_data = verify_res.get_json()
        self.assertTrue(v_data['success'])
        order_id = v_data['order_id']
        print(f"  [OK] Payment verified. Order #{v_data['order_number']} created (ID: {order_id})")

        # Step 3: Validate database state
        with self.app.app_context():
            order = Order.query.get(order_id)
            self.assertIsNotNone(order)
            self.assertEqual(order.payment_method, 'Razorpay')
            self.assertEqual(order.payment_status, 'Paid')
            self.assertEqual(order.razorpay_order_id, rzp_order_id)
            self.assertEqual(order.razorpay_payment_id, 'pay_demo_test_9988')
            self.assertEqual(order.total_amount, 1050.0)

            # Check inventory decrement: 10 - 3 = 7
            comp = Component.query.get(self.comp_id)
            self.assertEqual(comp.quantity, 7)
            print(f"  [OK] Component stock decremented from 10 to {comp.quantity}")

            # Check cart is emptied
            user_cart = CartItem.query.filter_by(user_id=self.user_id).all()
            self.assertEqual(len(user_cart), 0)
            print("  [OK] User cart emptied after successful payment")

        # Step 4: Verify Order Details Page Renders Payment Info
        detail_res = self.client.get(f'/orders/{order_id}')
        self.assertEqual(detail_res.status_code, 200)
        html = detail_res.data.decode('utf-8')
        self.assertIn('Razorpay', html)
        self.assertIn('Paid', html)
        self.assertIn('pay_demo_test_9988', html)
        print("  [OK] Customer order details page displays Payment Method, Paid status & Reference ID")

    def test_07_admin_orders_and_order_detail_view(self):
        print("\n[Test 7] Admin Order Views Displaying Payment Method & Status")
        self.login_user()

        with self.app.app_context():
            cart_item = CartItem(user_id=self.user_id, component_id=self.comp_id, quantity=1)
            db.session.add(cart_item)
            db.session.commit()

        # Place an order
        verify_res = self.client.post('/checkout/razorpay/verify', json={
            'razorpay_order_id': 'order_demo_admin_check',
            'razorpay_payment_id': 'pay_demo_admin_777',
            'razorpay_signature': 'demo_sig_admin_777',
            'customer_name': 'Razorpay Test Admin Check',
            'email': 'buyer@example.com',
            'phone': '9876543210',
            'address': '456 Tech Park',
            'city': 'Pune',
            'state': 'Maharashtra',
            'pincode': '411001'
        })
        order_id = verify_res.get_json()['order_id']

        # Log in as admin and view orders list
        self.login_admin()
        admin_list_res = self.client.get('/admin/orders')
        self.assertEqual(admin_list_res.status_code, 200)
        admin_list_html = admin_list_res.data.decode('utf-8')
        self.assertIn('Razorpay', admin_list_html)
        self.assertIn('Paid', admin_list_html)
        print("  [OK] Admin orders table displays Payment column with 'Paid' badge and 'Razorpay'")

        # View admin order details
        admin_detail_res = self.client.get(f'/admin/orders/{order_id}')
        self.assertEqual(admin_detail_res.status_code, 200)
        admin_detail_html = admin_detail_res.data.decode('utf-8')
        self.assertIn('pay_demo_admin_777', admin_detail_html)
        self.assertIn('Razorpay Payment ID', admin_detail_html)
        print("  [OK] Admin order detail displays Razorpay Payment ID and Paid status")

    def test_08_component_price_form_fields(self):
        print("\n[Test 8] Add and Edit Component Forms Include Price Field")
        self.login_user()

        # Check Add Component GET form has price field
        add_get = self.client.get('/components/add')
        self.assertEqual(add_get.status_code, 200)
        add_html = add_get.data.decode('utf-8')
        self.assertIn('name="price"', add_html)
        self.assertIn('Price (₹)', add_html)
        print("  [OK] Add Component form includes Price (₹) input")

        # Check Edit Component GET form has price field
        edit_get = self.client.get(f'/components/{self.comp_id}/edit')
        self.assertEqual(edit_get.status_code, 200)
        edit_html = edit_get.data.decode('utf-8')
        self.assertIn('name="price"', edit_html)
        self.assertIn(str(int(self.comp_price)), edit_html)
        print(f"  [OK] Edit Component form displays current price ₹{int(self.comp_price)}")

        # Post edit with new price ₹420
        edit_post = self.client.post(f'/components/{self.comp_id}/edit', data={
            'name': 'Razorpay Test Microcontroller ESP32 Updated',
            'category': 'Microcontrollers',
            'quantity': '8',
            'price': '420',
            'condition': 'Excellent',
            'status': 'Available',
            'estimated_weight': '22',
            'description': 'Updated price test'
        }, follow_redirects=True)
        self.assertEqual(edit_post.status_code, 200)

        with self.app.app_context():
            updated = Component.query.get(self.comp_id)
            self.assertEqual(updated.price, 420.0)
            self.assertEqual(updated.quantity, 8)
            print("  [OK] Component price updated to ₹420.0 in database")


if __name__ == '__main__':
    print("=" * 65)
    print("RUNNING SECONDLIFE RAZORPAY PAYMENT & PRICING TESTS")
    print("=" * 65)
    unittest.main()
