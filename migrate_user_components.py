"""
Safe SQLite Migration: Add user_components table and backfill user inventory.
Preserves all existing data in users, projects, components, orders, order_items, etc.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

def migrate():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    print(f"Connecting to database: {DB_PATH}")

    # Check if user_components table already exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_components'")
    exists = cur.fetchone() is not None

    if not exists:
        print("Creating table: user_components...")
        cur.execute("""
            CREATE TABLE user_components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                component_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (component_id) REFERENCES components(id) ON DELETE CASCADE,
                CONSTRAINT uq_user_component UNIQUE (user_id, component_id)
            )
        """)
        print("[OK] user_components table created.")
    else:
        print("user_components table already exists.")

    # Backfill:
    # 1. Any components listed by users directly (e.g. Rahul's baseline components)
    cur.execute("SELECT id, user_id, quantity, status FROM components WHERE user_id IS NOT NULL")
    comp_rows = cur.fetchall()
    backfilled_listed = 0
    for comp_id, user_id, qty, status in comp_rows:
        if status == 'Available' and qty and qty > 0:
            cur.execute("""
                INSERT OR IGNORE INTO user_components (user_id, component_id, quantity)
                VALUES (?, ?, ?)
            """, (user_id, comp_id, qty))
            backfilled_listed += 1

    print(f"[OK] Backfilled {backfilled_listed} available user-listed components into user_components.")

    # 2. Any past verified Paid orders
    cur.execute("""
        SELECT o.user_id, oi.component_id, oi.quantity
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        WHERE o.payment_status = 'Paid' AND oi.component_id IS NOT NULL
    """)
    paid_items = cur.fetchall()
    backfilled_purchases = 0
    for uid, cid, qty in paid_items:
        # Check if row already exists
        cur.execute("SELECT id, quantity FROM user_components WHERE user_id = ? AND component_id = ?", (uid, cid))
        row = cur.fetchone()
        if row:
            pass
        else:
            cur.execute("""
                INSERT INTO user_components (user_id, component_id, quantity)
                VALUES (?, ?, ?)
            """, (uid, cid, qty))
            backfilled_purchases += 1

    print(f"[OK] Backfilled {backfilled_purchases} purchased components from paid orders.")

    con.commit()
    con.close()
    print("Migration completed successfully!")

if __name__ == '__main__':
    migrate()
