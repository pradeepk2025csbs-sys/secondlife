"""
Database Cleanup Script for SECONDLIFE
Safely and idempotently removes automated test fixtures while preserving all real data:
- Removes test components (e.g. 'Marketplace Test Sensor%')
- Removes automated test orders and order items created by test suites
- Preserves all real hardware components (Arduino, Raspberry Pi, ESP32, sensors, motors, etc.)
- Preserves all real users, projects, real orders, payment configurations, and reuse history
"""

import os
import sys
import sqlite3

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'database.db')

def cleanup_database():
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Identify test components
    cursor.execute("""
        SELECT id, name, category, quantity, price, status, user_id 
        FROM components 
        WHERE name LIKE '%Test Sensor%' OR name LIKE 'Marketplace Test%'
    """)
    test_components = cursor.fetchall()
    test_comp_ids = [c[0] for c in test_components]
    print(f"\n[Step 1] Identified {len(test_components)} test component records:")
    for comp in test_components:
        print(f"  - ID {comp[0]}: '{comp[1]}' ({comp[2]}), Stock: {comp[3]}, Price: ₹{comp[4]}, Status: {comp[5]}")

    if not test_comp_ids:
        print("  ✓ No test components found. Database is already clean.")
    else:
        id_placeholder = ','.join('?' for _ in test_comp_ids)

        # 2. Check referencing order items
        cursor.execute(f"""
            SELECT id, order_id, component_id, component_name, quantity, unit_price
            FROM order_items
            WHERE component_id IN ({id_placeholder})
        """, test_comp_ids)
        ref_items = cursor.fetchall()
        print(f"\n[Step 2] Found {len(ref_items)} order items referencing test components:")
        
        test_order_ids_to_delete = []
        for item in ref_items:
            item_id, order_id, comp_id, comp_name, qty, price = item
            # Check the order
            cursor.execute("SELECT id, order_number, customer_name, total_amount FROM orders WHERE id = ?", (order_id,))
            order = cursor.fetchone()
            if order:
                ord_id, ord_num, cust_name, total = order
                print(f"  - OrderItem ID {item_id}: '{comp_name}' in Order #{ord_num} (Customer: '{cust_name}', Total: ₹{total})")
                if "Rahul Sharma" in cust_name and total == 750.0:
                    test_order_ids_to_delete.append(ord_id)
                elif "Razorpay Test" in cust_name:
                    test_order_ids_to_delete.append(ord_id)
                else:
                    # User order (e.g. Pradeep) - unlink component_id so the order history is preserved
                    print(f"    -> Keeping real order #{ord_num} (unlinking component foreign key to NULL)")
                    cursor.execute("UPDATE order_items SET component_id = NULL WHERE id = ?", (item_id,))

        test_order_ids_to_delete = list(set(test_order_ids_to_delete))

        # 3. Delete automated test orders and their order items
        if test_order_ids_to_delete:
            ord_placeholder = ','.join('?' for _ in test_order_ids_to_delete)
            print(f"\n[Step 3] Deleting {len(test_order_ids_to_delete)} automated test orders:")
            cursor.execute(f"DELETE FROM order_items WHERE order_id IN ({ord_placeholder})", test_order_ids_to_delete)
            deleted_items = cursor.rowcount
            cursor.execute(f"DELETE FROM orders WHERE id IN ({ord_placeholder})", test_order_ids_to_delete)
            deleted_orders = cursor.rowcount
            print(f"  ✓ Deleted {deleted_orders} test orders and {deleted_items} test order items")

        # 4. Clean cart items referencing test components if any
        cursor.execute(f"DELETE FROM cart_items WHERE component_id IN ({id_placeholder})", test_comp_ids)
        deleted_cart = cursor.rowcount
        if deleted_cart > 0:
            print(f"  ✓ Deleted {deleted_cart} cart items referencing test components")

        # 5. Delete the test components
        cursor.execute(f"DELETE FROM components WHERE id IN ({id_placeholder})", test_comp_ids)
        deleted_comps = cursor.rowcount
        print(f"\n[Step 4] Deleted {deleted_comps} test components from components table")

    conn.commit()

    # 6. Verification of real records
    print("\n" + "=" * 60)
    print("VERIFICATION OF PRESERVED PRODUCTION & DEMO DATA")
    print("=" * 60)
    cursor.execute("SELECT count(*) FROM components")
    total_comps = cursor.fetchone()[0]
    cursor.execute("SELECT id, name, category, quantity, price, status FROM components")
    remaining_comps = cursor.fetchall()
    print(f"Total remaining components: {total_comps}")
    for c in remaining_comps:
        print(f"  - #{c[0]}: {c[1]} ({c[2]}) - Stock: {c[3]}, Price: ₹{c[4]}, Status: {c[5]}")

    cursor.execute("SELECT count(*) FROM users")
    total_users = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM projects")
    total_projects = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM orders")
    total_orders = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM reuse_history")
    total_reuses = cursor.fetchone()[0]

    print(f"\nPreserved Database Summary:")
    print(f"  • Components: {total_comps} real components")
    print(f"  • Users: {total_users} users")
    print(f"  • Projects: {total_projects} projects")
    print(f"  • Orders: {total_orders} real orders")
    print(f"  • Reuse History: {total_reuses} reuse records")

    # Check for any remaining test components
    cursor.execute("SELECT count(*) FROM components WHERE name LIKE '%Test%'")
    test_rem = cursor.fetchone()[0]
    print(f"\nRemaining components matching '%Test%': {test_rem} (Expected: 0)")
    assert test_rem == 0, f"Error: {test_rem} test components still remain!"

    conn.close()
    print("\n🎉 Database cleanup successfully completed!")


if __name__ == '__main__':
    cleanup_database()
