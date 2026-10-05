"""
SECONDLIFE – Database Seed Script
Populates the database with sample data for demonstration.

Usage:
    python seed.py
"""

import os
import sys

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Ensure the app directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models.models import db, User, Component, Project, ProjectComponent, SavedProject, ReuseHistory
from werkzeug.security import generate_password_hash


def seed_database():
    with app.app_context():
        # Drop and recreate tables for a fresh seed
        db.drop_all()
        db.create_all()

        print('🌱 Seeding database...')

        # ─── USERS ───
        admin = User(
            name='Admin',
            email='admin@secondlife.com',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )

        user1 = User(
            name='Rahul Sharma',
            email='rahul@example.com',
            password_hash=generate_password_hash('password123'),
            role='user'
        )

        user2 = User(
            name='Priya Patel',
            email='priya@example.com',
            password_hash=generate_password_hash('password123'),
            role='user'
        )

        user3 = User(
            name='Amit Kumar',
            email='amit@example.com',
            password_hash=generate_password_hash('password123'),
            role='user'
        )

        db.session.add_all([admin, user1, user2, user3])
        db.session.flush()
        print('  ✓ Users created')

        # ─── COMPONENTS (for demo users) ───
        components = [
            # Rahul's components
            Component(user_id=user1.id, name='Arduino Uno', category='Microcontroller',
                      quantity=2, price=450.0, condition='Good', estimated_weight=25,
                      description='Working Arduino Uno R3 board with USB cable.', status='Available'),
            Component(user_id=user1.id, name='Ultrasonic Sensor', category='Sensor',
                      quantity=2, price=90.0, condition='Good', estimated_weight=10,
                      description='HC-SR04 ultrasonic distance sensor module.', status='Available'),
            Component(user_id=user1.id, name='Servo Motor', category='Motor',
                      quantity=3, price=120.0, condition='Good', estimated_weight=40,
                      description='SG90 micro servo motor, 180 degree rotation.', status='Available'),
            Component(user_id=user1.id, name='Jumper Wires', category='Cable',
                      quantity=5, price=50.0, condition='New', estimated_weight=15,
                      description='Pack of male-to-male and male-to-female jumper wires.', status='Available'),
            Component(user_id=user1.id, name='Relay Module', category='Power',
                      quantity=2, price=80.0, condition='Good', estimated_weight=20,
                      description='Single channel 5V relay module with optocoupler.', status='Available'),
            Component(user_id=user1.id, name='Soil Moisture Sensor', category='Sensor',
                      quantity=1, price=60.0, condition='Used', estimated_weight=8,
                      description='Analog soil moisture sensor with probe.', status='Available'),
            Component(user_id=user1.id, name='Water Pump', category='Motor',
                      quantity=1, price=180.0, condition='Good', estimated_weight=50,
                      description='Mini submersible water pump, 3-6V DC.', status='Available'),
            Component(user_id=user1.id, name='LED Pack', category='Display',
                      quantity=10, price=40.0, condition='New', estimated_weight=5,
                      description='Assorted color LED pack (red, green, blue, yellow).', status='Available'),

            # Priya's components
            Component(user_id=user2.id, name='Raspberry Pi 3B', category='Microcontroller',
                      quantity=1, price=3500.0, condition='Good', estimated_weight=45,
                      description='Raspberry Pi 3 Model B with case.', status='Available'),
            Component(user_id=user2.id, name='PIR Motion Sensor', category='Sensor',
                      quantity=2, price=100.0, condition='Good', estimated_weight=12,
                      description='HC-SR04 ultrasonic / infrared motion sensor module.', status='Available'),
            Component(user_id=user2.id, name='Buzzer', category='Other',
                      quantity=3, price=30.0, condition='New', estimated_weight=5,
                      description='5V active buzzer module.', status='Available'),
            Component(user_id=user2.id, name='LCD Display 16x2', category='Display',
                      quantity=1, price=150.0, condition='Good', estimated_weight=30,
                      description='16x2 character LCD display with I2C backpack.', status='Available'),
            Component(user_id=user2.id, name='DHT11 Temperature Sensor', category='Sensor',
                      quantity=2, price=80.0, condition='Good', estimated_weight=8,
                      description='DHT11 temperature and humidity sensor.', status='Available'),
            Component(user_id=user2.id, name='Breadboard', category='PCB',
                      quantity=2, price=100.0, condition='Good', estimated_weight=35,
                      description='830-point solderless breadboard.', status='Available'),
            Component(user_id=user2.id, name='ESP8266 WiFi Module', category='Communication',
                      quantity=1, price=250.0, condition='Good', estimated_weight=10,
                      description='NodeMCU ESP8266 WiFi development board.', status='Available'),
            Component(user_id=user2.id, name='LDR Sensor', category='Sensor',
                      quantity=3, price=40.0, condition='New', estimated_weight=3,
                      description='Light dependent resistor (photoresistor).', status='Available'),

            # Amit's components
            Component(user_id=user3.id, name='Arduino Nano', category='Microcontroller',
                      quantity=2, price=300.0, condition='Good', estimated_weight=15,
                      description='Arduino Nano V3 with mini USB cable.', status='Available'),
            Component(user_id=user3.id, name='DC Motor', category='Motor',
                      quantity=4, price=180.0, condition='Used', estimated_weight=35,
                      description='Small DC motor with gear, 3-12V.', status='Available'),
            Component(user_id=user3.id, name='Motor Driver L298N', category='Motor',
                      quantity=1, price=150.0, condition='Good', estimated_weight=30,
                      description='L298N dual H-bridge motor driver module.', status='Available'),
            Component(user_id=user3.id, name='IR Sensor', category='Sensor',
                      quantity=3, price=80.0, condition='Good', estimated_weight=8,
                      description='IR infrared obstacle avoidance sensor module.', status='Available'),
            Component(user_id=user3.id, name='Battery Holder', category='Power',
                      quantity=2, price=70.0, condition='New', estimated_weight=20,
                      description='4x AA battery holder with switch and wires.', status='Available'),
            Component(user_id=user3.id, name='Resistor Pack', category='Other',
                      quantity=1, price=50.0, condition='New', estimated_weight=10,
                      description='Assorted resistor pack (220Ω to 10kΩ).', status='Available'),
            Component(user_id=user3.id, name='Capacitor Pack', category='Other',
                      quantity=1, price=60.0, condition='New', estimated_weight=8,
                      description='Assorted ceramic and electrolytic capacitors.', status='Available'),
            Component(user_id=user3.id, name='Jumper Wires', category='Cable',
                      quantity=3, price=50.0, condition='Good', estimated_weight=15,
                      description='Jumper wire bundle for prototyping.', status='Available'),
        ]

        db.session.add_all(components)
        db.session.flush()
        print(f'  ✓ {len(components)} components created')

        # ─── PROJECTS ───
        projects_data = [
            {
                'title': 'Smart Dustbin',
                'description': 'Build an automatic dustbin that opens its lid when someone approaches. '
                               'Uses an ultrasonic sensor to detect presence and a servo motor to '
                               'control the lid. Great for promoting contactless waste disposal and hygiene.',
                'category': 'IoT',
                'difficulty': 'Beginner',
                'estimated_cost': 300,
                'estimated_waste_reduction': 250,
                'requirements': [
                    ('Arduino Uno', 'Microcontroller', 1),
                    ('Ultrasonic Sensor', 'Sensor', 1),
                    ('Servo Motor', 'Motor', 1),
                    ('Jumper Wires', 'Cable', 1),
                ]
            },
            {
                'title': 'Automatic Plant Watering System',
                'description': 'Create a system that automatically waters your plants based on soil '
                               'moisture levels. The soil moisture sensor reads humidity, and when it '
                               'drops below a threshold, the relay activates the water pump.',
                'category': 'Automation',
                'difficulty': 'Beginner',
                'estimated_cost': 400,
                'estimated_waste_reduction': 200,
                'requirements': [
                    ('Arduino Uno', 'Microcontroller', 1),
                    ('Soil Moisture Sensor', 'Sensor', 1),
                    ('Water Pump', 'Motor', 1),
                    ('Relay Module', 'Power', 1),
                    ('Jumper Wires', 'Cable', 1),
                ]
            },
            {
                'title': 'Smart Parking System',
                'description': 'Build a parking system that detects whether a parking slot is occupied '
                               'using IR sensors. An LCD display shows the number of available spots. '
                               'Useful for small parking lots or garage projects.',
                'category': 'IoT',
                'difficulty': 'Intermediate',
                'estimated_cost': 600,
                'estimated_waste_reduction': 300,
                'requirements': [
                    ('Arduino Uno', 'Microcontroller', 1),
                    ('IR Sensor', 'Sensor', 3),
                    ('LCD Display 16x2', 'Display', 1),
                    ('LED Pack', 'Display', 1),
                    ('Jumper Wires', 'Cable', 1),
                ]
            },
            {
                'title': 'Line Following Robot',
                'description': 'Build a robot that follows a black line on a white surface using '
                               'IR sensors. The motors are controlled by a motor driver based on '
                               'sensor readings. A classic robotics project for beginners.',
                'category': 'Robotics',
                'difficulty': 'Intermediate',
                'estimated_cost': 700,
                'estimated_waste_reduction': 350,
                'requirements': [
                    ('Arduino Uno', 'Microcontroller', 1),
                    ('IR Sensor', 'Sensor', 2),
                    ('DC Motor', 'Motor', 2),
                    ('Motor Driver L298N', 'Motor', 1),
                    ('Battery Holder', 'Power', 1),
                    ('Jumper Wires', 'Cable', 1),
                ]
            },
            {
                'title': 'Obstacle Avoiding Robot',
                'description': 'Create a robot that navigates around obstacles using an ultrasonic '
                               'sensor mounted on a servo motor for scanning. The robot changes '
                               'direction when it detects an obstacle ahead.',
                'category': 'Robotics',
                'difficulty': 'Intermediate',
                'estimated_cost': 800,
                'estimated_waste_reduction': 400,
                'requirements': [
                    ('Arduino Uno', 'Microcontroller', 1),
                    ('Ultrasonic Sensor', 'Sensor', 1),
                    ('Servo Motor', 'Motor', 1),
                    ('DC Motor', 'Motor', 2),
                    ('Motor Driver L298N', 'Motor', 1),
                    ('Battery Holder', 'Power', 1),
                    ('Jumper Wires', 'Cable', 1),
                ]
            },
            {
                'title': 'Home Automation System',
                'description': 'Control home appliances (lights, fans) remotely using a smartphone '
                               'via WiFi. Uses ESP8266 as the WiFi module and relays to switch '
                               'appliances on and off.',
                'category': 'Smart Home',
                'difficulty': 'Intermediate',
                'estimated_cost': 500,
                'estimated_waste_reduction': 280,
                'requirements': [
                    ('ESP8266 WiFi Module', 'Communication', 1),
                    ('Relay Module', 'Power', 2),
                    ('LED Pack', 'Display', 1),
                    ('Jumper Wires', 'Cable', 1),
                    ('Breadboard', 'PCB', 1),
                ]
            },
            {
                'title': 'Weather Monitoring Station',
                'description': 'Build a weather station that monitors temperature, humidity, and '
                               'displays the data on an LCD screen. Can be extended with WiFi '
                               'to log data to the cloud.',
                'category': 'IoT',
                'difficulty': 'Beginner',
                'estimated_cost': 350,
                'estimated_waste_reduction': 180,
                'requirements': [
                    ('Arduino Uno', 'Microcontroller', 1),
                    ('DHT11 Temperature Sensor', 'Sensor', 1),
                    ('LCD Display 16x2', 'Display', 1),
                    ('Breadboard', 'PCB', 1),
                    ('Jumper Wires', 'Cable', 1),
                ]
            },
            {
                'title': 'Smart Door Lock',
                'description': 'Create a door lock system using a servo motor and password input. '
                               'A 4x4 keypad allows users to enter a PIN code. The servo locks or '
                               'unlocks the door. An LCD provides visual feedback.',
                'category': 'Smart Home',
                'difficulty': 'Intermediate',
                'estimated_cost': 450,
                'estimated_waste_reduction': 220,
                'requirements': [
                    ('Arduino Uno', 'Microcontroller', 1),
                    ('Servo Motor', 'Motor', 1),
                    ('LCD Display 16x2', 'Display', 1),
                    ('Buzzer', 'Other', 1),
                    ('Jumper Wires', 'Cable', 1),
                ]
            },
            {
                'title': 'Mini Security Alarm',
                'description': 'Build a motion-detecting security alarm using a PIR sensor. '
                               'When motion is detected, the buzzer sounds an alarm and an LED '
                               'flashes. Simple but effective intruder detection.',
                'category': 'Smart Home',
                'difficulty': 'Beginner',
                'estimated_cost': 200,
                'estimated_waste_reduction': 150,
                'requirements': [
                    ('Arduino Uno', 'Microcontroller', 1),
                    ('PIR Motion Sensor', 'Sensor', 1),
                    ('Buzzer', 'Other', 1),
                    ('LED Pack', 'Display', 1),
                    ('Jumper Wires', 'Cable', 1),
                ]
            },
            {
                'title': 'Automatic Night Lamp',
                'description': 'Create a lamp that automatically turns on when it gets dark '
                               'and turns off in daylight. Uses an LDR to detect ambient light '
                               'level and controls an LED or relay accordingly.',
                'category': 'Electronics',
                'difficulty': 'Beginner',
                'estimated_cost': 100,
                'estimated_waste_reduction': 120,
                'requirements': [
                    ('Arduino Uno', 'Microcontroller', 1),
                    ('LDR Sensor', 'Sensor', 1),
                    ('LED Pack', 'Display', 1),
                    ('Resistor Pack', 'Other', 1),
                    ('Jumper Wires', 'Cable', 1),
                ]
            },
            {
                'title': 'Digital Temperature Monitor',
                'description': 'Monitor room temperature and humidity in real-time on an LCD '
                               'display. Sounds an alert if temperature exceeds a threshold. '
                               'Great for server rooms or greenhouses.',
                'category': 'Education',
                'difficulty': 'Beginner',
                'estimated_cost': 250,
                'estimated_waste_reduction': 160,
                'requirements': [
                    ('Arduino Uno', 'Microcontroller', 1),
                    ('DHT11 Temperature Sensor', 'Sensor', 1),
                    ('LCD Display 16x2', 'Display', 1),
                    ('Buzzer', 'Other', 1),
                    ('Jumper Wires', 'Cable', 1),
                ]
            },
            {
                'title': 'IoT Environment Monitor',
                'description': 'Build a WiFi-connected environment monitor that tracks temperature, '
                               'humidity, and light levels. Data is sent to a cloud dashboard for '
                               'remote monitoring using ESP8266.',
                'category': 'IoT',
                'difficulty': 'Advanced',
                'estimated_cost': 550,
                'estimated_waste_reduction': 300,
                'requirements': [
                    ('ESP8266 WiFi Module', 'Communication', 1),
                    ('DHT11 Temperature Sensor', 'Sensor', 1),
                    ('LDR Sensor', 'Sensor', 1),
                    ('LCD Display 16x2', 'Display', 1),
                    ('Breadboard', 'PCB', 1),
                    ('Jumper Wires', 'Cable', 1),
                ]
            },
        ]

        for pdata in projects_data:
            project = Project(
                title=pdata['title'],
                description=pdata['description'],
                category=pdata['category'],
                difficulty=pdata['difficulty'],
                estimated_cost=pdata['estimated_cost'],
                estimated_waste_reduction=pdata['estimated_waste_reduction']
            )
            db.session.add(project)
            db.session.flush()

            for req_name, req_cat, req_qty in pdata['requirements']:
                pc = ProjectComponent(
                    project_id=project.id,
                    component_name=req_name,
                    category=req_cat,
                    required_quantity=req_qty
                )
                db.session.add(pc)

        print(f'  ✓ {len(projects_data)} projects created with requirements')

        # ─── SAMPLE SAVED PROJECTS ───
        sp1 = SavedProject(user_id=user1.id, project_id=1)  # Rahul saved Smart Dustbin
        sp2 = SavedProject(user_id=user1.id, project_id=2)  # Rahul saved Plant Watering
        sp3 = SavedProject(user_id=user2.id, project_id=7)  # Priya saved Weather Station
        db.session.add_all([sp1, sp2, sp3])

        # ─── SAMPLE REUSE HISTORY (some demo completed projects) ───
        # Priya completed Mini Security Alarm
        rh1 = ReuseHistory(user_id=user2.id, component_id=10, project_id=9, waste_reduced=12)
        rh2 = ReuseHistory(user_id=user2.id, component_id=11, project_id=9, waste_reduced=5)
        db.session.add_all([rh1, rh2])

        print('  ✓ Sample saved projects and reuse history created')

        db.session.commit()

        print()
        print('✅ Database seeded successfully!')
        print()
        print('Demo Accounts:')
        print('  Admin:  admin@secondlife.com / admin123')
        print('  User 1: rahul@example.com / password123')
        print('  User 2: priya@example.com / password123')
        print('  User 3: amit@example.com / password123')
        print()


if __name__ == '__main__':
    seed_database()
