import sqlite3

def run_migration():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    # 1. Check & add seller_id to components
    comp_cols = [r[1] for r in cur.execute('PRAGMA table_info(components)').fetchall()]
    print('Existing components columns:', comp_cols)

    if 'seller_id' not in comp_cols:
        print('Adding seller_id column to components table...')
        cur.execute('ALTER TABLE components ADD COLUMN seller_id INTEGER REFERENCES users(id)')
        cur.execute('UPDATE components SET seller_id = user_id WHERE seller_id IS NULL')
        conn.commit()
        print('seller_id added and populated for components!')
    else:
        print('seller_id already exists in components.')
        cur.execute('UPDATE components SET seller_id = user_id WHERE seller_id IS NULL')
        conn.commit()

    # 2. Check & add seller_id and status to order_items
    item_cols = [r[1] for r in cur.execute('PRAGMA table_info(order_items)').fetchall()]
    print('Existing order_items columns:', item_cols)

    if 'seller_id' not in item_cols:
        print('Adding seller_id column to order_items table...')
        cur.execute('ALTER TABLE order_items ADD COLUMN seller_id INTEGER REFERENCES users(id)')
        conn.commit()
        print('seller_id added to order_items!')

    if 'status' not in item_cols:
        print('Adding status column to order_items table...')
        cur.execute("ALTER TABLE order_items ADD COLUMN status VARCHAR(30) DEFAULT 'Confirmed'")
        conn.commit()
        print('status added to order_items!')

    # Populate seller_id for existing order_items
    cur.execute('''
        UPDATE order_items
        SET seller_id = (
            SELECT seller_id FROM components WHERE components.id = order_items.component_id
        )
        WHERE seller_id IS NULL AND component_id IS NOT NULL
    ''')
    # For any remaining without seller_id, assign to admin (id=1)
    cur.execute('UPDATE order_items SET seller_id = 1 WHERE seller_id IS NULL')
    conn.commit()
    print('Populated seller_id for existing order_items!')

    # Verify
    print('\n=== Verifying updated schema ===')
    print('components:', [r[1] for r in cur.execute('PRAGMA table_info(components)').fetchall()])
    print('order_items:', [r[1] for r in cur.execute('PRAGMA table_info(order_items)').fetchall()])
    conn.close()

if __name__ == '__main__':
    run_migration()
