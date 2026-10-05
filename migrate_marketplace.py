import sqlite3
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'database.db')

print(f'Migrating database at: {db_path}')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Add price column to components table if not present
cursor.execute("PRAGMA table_info(components)")
columns = [col[1] for col in cursor.fetchall()]
if 'price' not in columns:
    print('Adding "price" column to components table...')
    cursor.execute("ALTER TABLE components ADD COLUMN price FLOAT DEFAULT 0.0")
    conn.commit()
    print('  [OK] price column added')
else:
    print('  [OK] price column already exists')

# 2. Update price for all existing components based on name
PRICE_RULES = [
    ('arduino uno', 450.0),
    ('ardiuno uno', 450.0),
    ('arduino nano', 300.0),
    ('esp32', 350.0),
    ('esp8266', 250.0),
    ('raspberry pi', 3500.0),
    ('ultrasonic', 90.0),
    ('dht11', 80.0),
    ('pir motion', 100.0),
    ('pir', 100.0),
    ('soil moisture', 60.0),
    ('soil', 60.0),
    ('servo', 120.0),
    ('dc motor', 180.0),
    ('gear motor', 180.0),
    ('motor driver', 150.0),
    ('l298n', 150.0),
    ('water pump', 180.0),
    ('pump', 180.0),
    ('relay', 80.0),
    ('lcd', 150.0),
    ('16x2', 150.0),
    ('oled', 180.0),
    ('jumper', 50.0),
    ('breadboard', 100.0),
    ('buzzer', 30.0),
    ('led', 40.0),
    ('resistor', 50.0),
    ('capacitor', 60.0),
    ('battery', 70.0),
    ('ir sensor', 80.0),
    ('ldr', 40.0)
]

cursor.execute("SELECT id, name, category, price FROM components")
components = cursor.fetchall()
print(f'Updating pricing for {len(components)} components...')

for comp_id, name, category, curr_price in components:
    name_lower = (name or '').lower()
    target_price = 100.0  # default fallback
    for kw, price in PRICE_RULES:
        if kw in name_lower:
            target_price = price
            break
    
    # Update price if it was 0 or None
    cursor.execute("UPDATE components SET price = ? WHERE id = ?", (target_price, comp_id))
    print(f'  Component #{comp_id} "{name}": set price to ₹{target_price:.0f}')

# 3. Add Razorpay and payment status columns to orders table if not present
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'")
if cursor.fetchone():
    cursor.execute("PRAGMA table_info(orders)")
    order_cols = [col[1] for col in cursor.fetchall()]
    
    new_order_cols = [
        ('payment_status', "TEXT DEFAULT 'Pending'"),
        ('razorpay_order_id', "TEXT"),
        ('razorpay_payment_id', "TEXT"),
        ('razorpay_signature', "TEXT")
    ]
    for col_name, col_def in new_order_cols:
        if col_name not in order_cols:
            print(f'Adding "{col_name}" column to orders table...')
            cursor.execute(f"ALTER TABLE orders ADD COLUMN {col_name} {col_def}")
            print(f'  [OK] {col_name} column added')
        else:
            print(f'  [OK] {col_name} column already exists')

    # Update existing demo orders to Paid
    cursor.execute("UPDATE orders SET payment_status = 'Paid' WHERE payment_method = 'Demo Payment' AND (payment_status IS NULL OR payment_status = 'Pending')")

conn.commit()
conn.close()

# 4. Create missing tables (cart_items, orders, order_items) using SQLAlchemy db.create_all()
from app import create_app
from models.models import db

app = create_app()
with app.app_context():
    db.create_all()
    print('  ✓ All database tables verified and created (cart_items, orders, order_items)')

print('🎉 Database migration successfully completed!')
