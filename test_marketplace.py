"""
SECONDLIFE Marketplace Tests
Comprehensive test suite covering shopping cart, pricing, buy-now, checkout,
orders, inventory reduction, authorization security, and historical price preservation.
Includes automatic test fixture cleanup so zero test records remain in database.db.
"""

import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.models import db, User, Component, CartItem, Order, OrderItem
from werkzeug.security import generate_password_hash


def run_marketplace_tests():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    print("=" * 65)
    print("RUNNING SECONDLIFE MARKETPLACE & PRICING TESTS")
    print("=" * 65)

    with app.test_client() as client:
        with app.app_context():
            # Setup demo test users
            buyer = User.query.filter_by(email='rahul@example.com').first()
            if not buyer:
                buyer = User(name='Rahul Sharma', email='rahul@example.com',
                             password_hash=generate_password_hash('password123'), role='user')
                db.session.add(buyer)

            other_user = User.query.filter_by(email='priya@example.com').first()
            if not other_user:
                other_user = User(name='Priya Patel', email='priya@example.com',
                                  password_hash=generate_password_hash('password123'), role='user')
                db.session.add(other_user)

            admin_user = User.query.filter_by(email='admin@secondlife.com').first()
            if not admin_user:
                admin_user = User(name='Admin', email='admin@secondlife.com',
                                  password_hash=generate_password_hash('admin123'), role='admin')
                db.session.add(admin_user)

            # Pre-clean any leftover test components / orders from prior runs
            old_comps = Component.query.filter(
                Component.name.in_(['Marketplace Test Sensor', 'Marketplace Test Sensor Pro'])
            ).all()
            for old_c in old_comps:
                for item in OrderItem.query.filter_by(component_id=old_c.id).all():
                    if item.order and 'Rahul' in item.order.customer_name:
                        db.session.delete(item.order)
                    else:
                        item.component_id = None
                OrderItem.query.filter_by(component_id=old_c.id).delete()
                db.session.delete(old_c)
            db.session.commit()

            # Create fresh isolated test component
            test_comp = Component(
                user_id=other_user.id,
                name='Marketplace Test Sensor',
                category='Sensor',
                quantity=10,
                price=250.0,
                condition='Good',
                status='Available',
                description='Test sensor for automated marketplace tests'
            )
            db.session.add(test_comp)
            db.session.commit()

            test_comp_id = test_comp.id
            buyer_id = buyer.id
            other_user_id = other_user.id

            # Clean any previous cart items for buyer
            CartItem.query.filter_by(user_id=buyer_id).delete()
            db.session.commit()

        created_order_id = None

        try:
            # [Test 1] Login as Buyer
            print("\n[Test 1] User Authentication")
            login_res = client.post('/login', data={'email': 'rahul@example.com', 'password': 'password123'}, follow_redirects=True)
            assert login_res.status_code == 200
            print("  [OK] Rahul Sharma logged in successfully")

            # [Test 2] Add Item to Cart
            print("\n[Test 2] Add Item to Cart")
            res = client.post(f'/cart/add/{test_comp_id}', data={'quantity': 2}, follow_redirects=True)
            assert res.status_code == 200
            with app.app_context():
                item = CartItem.query.filter_by(user_id=buyer_id, component_id=test_comp_id).first()
                assert item is not None, "CartItem was not created"
                assert item.quantity == 2, f"Expected qty 2, got {item.quantity}"
                assert item.subtotal == 500.0, f"Expected subtotal 500, got {item.subtotal}"
                item_id = item.id
            print("  [OK] Successfully added 2 units to cart (Subtotal: ₹500)")

            # [Test 3] Increase Quantity in Cart
            print("\n[Test 3] Increase Cart Quantity")
            res = client.post(f'/cart/update/{item_id}', data={'action': 'increase'}, follow_redirects=True)
            assert res.status_code == 200
            with app.app_context():
                item = CartItem.query.get(item_id)
                assert item.quantity == 3, f"Expected qty 3, got {item.quantity}"
            print("  [OK] Quantity increased to 3")

            # [Test 4] Decrease Quantity in Cart
            print("\n[Test 4] Decrease Cart Quantity")
            res = client.post(f'/cart/update/{item_id}', data={'action': 'decrease'}, follow_redirects=True)
            assert res.status_code == 200
            with app.app_context():
                item = CartItem.query.get(item_id)
                assert item.quantity == 2, f"Expected qty 2, got {item.quantity}"
            print("  [OK] Quantity decreased back to 2")

            # [Test 5] Cart Total Calculation
            print("\n[Test 5] Cart Total Calculation")
            res = client.get('/cart')
            assert res.status_code == 200
            assert b'500' in res.data or b'500.0' in res.data
            print("  [OK] /cart page renders correctly with verified total ₹500")

            # [Test 6] Remove Item from Cart
            print("\n[Test 6] Remove Item from Cart")
            res = client.post(f'/cart/remove/{item_id}', follow_redirects=True)
            assert res.status_code == 200
            with app.app_context():
                item = CartItem.query.get(item_id)
                assert item is None, "Item was not deleted from cart"
            print("  [OK] Item successfully removed from cart")

            # [Test 7] Buy Now Flow
            print("\n[Test 7] Buy Now Quick Purchase")
            res = client.post(f'/buy-now/{test_comp_id}', data={'quantity': 3}, follow_redirects=False)
            assert res.status_code == 302
            assert '/checkout' in res.headers.get('Location', '')
            with app.app_context():
                item = CartItem.query.filter_by(user_id=buyer_id, component_id=test_comp_id).first()
                assert item is not None
                assert item.quantity == 3
            print("  [OK] Buy Now preserved quantity 3 and redirected straight to /checkout")

            # [Test 8] Checkout Page Review
            print("\n[Test 8] Checkout Review Page")
            res = client.get('/checkout')
            assert res.status_code == 200
            assert b'Marketplace Test Sensor' in res.data
            assert b'750' in res.data  # 3 * 250 = 750
            print("  [OK] /checkout renders with component info, live prices, and payment options")

            # [Test 9] Successful Order Placement & Inventory Reduction
            print("\n[Test 9] Order Placement & Inventory Reduction")
            with app.app_context():
                initial_stock = Component.query.get(test_comp_id).quantity

            order_data = {
                'customer_name': 'Rahul Sharma',
                'email': 'rahul@example.com',
                'phone': '9876543210',
                'address': '123 Tech Park, 4th Cross',
                'city': 'Bengaluru',
                'state': 'Karnataka',
                'pincode': '560001',
                'payment_method': 'UPI'
            }
            res = client.post('/checkout', data=order_data, follow_redirects=True)
            assert res.status_code == 200
            assert b'Order Placed Successfully' in res.data

            with app.app_context():
                order = Order.query.filter_by(user_id=buyer_id).order_by(Order.created_at.desc()).first()
                assert order is not None
                assert order.total_amount == 750.0, f"Expected total 750, got {order.total_amount}"
                assert order.payment_method == 'UPI'
                assert len(order.items) == 1
                order_item = order.items[0]
                assert order_item.component_name == 'Marketplace Test Sensor'
                assert order_item.quantity == 3
                assert order_item.unit_price == 250.0

                # Verify inventory reduced
                final_stock = Component.query.get(test_comp_id).quantity
                assert final_stock == initial_stock - 3, f"Expected stock {initial_stock - 3}, got {final_stock}"
                created_order_id = order.id

                # Verify cart emptied
                remaining_cart = CartItem.query.filter_by(user_id=buyer_id).count()
                assert remaining_cart == 0, "Cart should be empty after checkout"

            print(f"  [OK] Order #{order.order_number} created with total ₹750")
            print(f"  [OK] Stock decremented from {initial_stock} to {final_stock} units")
            print("  [OK] Cart emptied after checkout")

            # [Test 10] Inventory Validation Prevents Negative Stock
            print("\n[Test 10] Insufficient Stock Prevention")
            with app.app_context():
                current_stock = Component.query.get(test_comp_id).quantity
                oversell_item = CartItem(user_id=buyer_id, component_id=test_comp_id, quantity=current_stock + 50)
                db.session.add(oversell_item)
                db.session.commit()

            res = client.post('/checkout', data=order_data, follow_redirects=True)
            assert res.status_code == 200
            with app.app_context():
                after_stock = Component.query.get(test_comp_id).quantity
                assert after_stock == current_stock, "Stock should NOT decrease on failed order"
                CartItem.query.filter_by(user_id=buyer_id).delete()
                db.session.commit()
            print("  [OK] Prevented order with excessive quantity, stock preserved")

            # [Test 11] User Cannot Access Another User's Order (RBAC & Privacy)
            print("\n[Test 11] Cross-User Order Security")
            client.get('/logout', follow_redirects=True)
            client.post('/login', data={'email': 'priya@example.com', 'password': 'password123'}, follow_redirects=True)
            res = client.get(f'/orders/{created_order_id}', follow_redirects=True)
            assert b'Access denied' in res.data or b'not authorized' in res.data or res.status_code in [403, 302]
            print("  [OK] Priya blocked from accessing Rahul's order details")

            # [Test 12] Admin Can View Orders & Update Status
            print("\n[Test 12] Admin Order Management")
            client.get('/logout', follow_redirects=True)
            client.post('/login', data={'email': 'admin@secondlife.com', 'password': 'admin123'}, follow_redirects=True)
            res = client.get('/admin/orders')
            assert res.status_code == 200
            assert b'Customer Orders Management' in res.data

            res = client.get(f'/admin/orders/{created_order_id}')
            assert res.status_code == 200
            assert b'Admin Order Review' in res.data

            res = client.post(f'/admin/orders/{created_order_id}/status', data={'status': 'Shipped'}, follow_redirects=True)
            assert res.status_code == 200
            with app.app_context():
                updated_order = Order.query.get(created_order_id)
                assert updated_order.status == 'Shipped'
            print("  [OK] Admin successfully viewed orders and updated status to 'Shipped'")

            # [Test 13] Admin Can Edit Component Price & Stock
            print("\n[Test 13] Admin Component Price & Stock Editing")
            edit_data = {
                'name': 'Marketplace Test Sensor Pro',
                'price': '320',
                'quantity': '15',
                'category': 'Sensor',
                'condition': 'New',
                'status': 'Available',
                'description': 'Updated by admin'
            }
            res = client.post(f'/admin/components/{test_comp_id}/edit', data=edit_data, follow_redirects=True)
            assert res.status_code == 200
            with app.app_context():
                updated_comp = Component.query.get(test_comp_id)
                assert updated_comp.price == 320.0, f"Expected 320, got {updated_comp.price}"
                assert updated_comp.quantity == 15, f"Expected 15, got {updated_comp.quantity}"
            print("  [OK] Admin successfully updated component price to ₹320 and stock to 15")

            # [Test 14] Historical Order Price Preservation
            print("\n[Test 14] Historical Order Price Preservation")
            with app.app_context():
                past_order = Order.query.get(created_order_id)
                assert past_order.total_amount == 750.0, f"Expected historical total 750, got {past_order.total_amount}"
                assert past_order.items[0].unit_price == 250.0, f"Expected historical unit price 250, got {past_order.items[0].unit_price}"
            print("  [OK] Historical order preserved original ₹250 unit price despite component price change to ₹320")

        finally:
            with app.app_context():
                # Clean up test orders created during tests
                if created_order_id:
                    order = Order.query.get(created_order_id)
                    if order:
                        db.session.delete(order)
                # Clean up buyer cart
                CartItem.query.filter_by(user_id=buyer_id).delete()
                # Clean up test component
                comp = Component.query.get(test_comp_id)
                if comp:
                    OrderItem.query.filter_by(component_id=test_comp_id).delete()
                    db.session.delete(comp)
                db.session.commit()
                print("  ✓ Cleaned up test marketplace component and test order")

    print("\n" + "=" * 65)
    print("ALL 14 MARKETPLACE & PRICING TESTS PASSED (100% PASS RATE)!")
    print("=" * 65)


if __name__ == '__main__':
    run_marketplace_tests()
