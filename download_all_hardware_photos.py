"""
Download authentic, real physical hardware product photographs for all SECONDLIFE components.
All images are public domain / CC-BY from Wikimedia Commons / Open Source Hardware.
"""

import os
import time
import urllib.request
import shutil

OUTPUT_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'images', 'components')
os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADERS = {
    'User-Agent': 'SecondLifeHardwareCatalog/1.0 (Educational open hardware project; contact: info@secondlife.local)'
}

DOWNLOAD_MAP = {
    'servo_motor.jpg': 'https://upload.wikimedia.org/wikipedia/commons/4/4d/Tower_Pro_SG90_micro_servo_motor.jpg',
    'ultrasonic_sensor.jpg': 'https://upload.wikimedia.org/wikipedia/commons/9/99/SparkFun_HC-SR04_Ultrasonic-Sensor_13959-01a.jpg',
    'relay_module.jpg': 'https://upload.wikimedia.org/wikipedia/commons/5/56/SRD-05VDC-SL-C_5V_one-channel_relay_module.jpg',
    'soil_moisture_sensor.jpg': 'https://upload.wikimedia.org/wikipedia/commons/a/a7/Soil_moisture_sensor.JPG',
    'water_pump.jpg': 'https://upload.wikimedia.org/wikipedia/commons/9/98/Submersible_pump_in_action.jpg',
    'esp32.jpg': 'https://upload.wikimedia.org/wikipedia/commons/2/20/ESP32_Espressif_ESP-WROOM-32_Dev_Board.jpg',
    'esp8266.jpg': 'https://upload.wikimedia.org/wikipedia/commons/f/f5/NodeMCU_Lua_Lol1n_V3.jpg',
    'raspberry_pi.jpg': 'https://upload.wikimedia.org/wikipedia/commons/d/d1/9815_-_Raspberry_Pi_3.jpg',
    'arduino_nano.jpg': 'https://upload.wikimedia.org/wikipedia/commons/6/6c/Arduino_Nano_V3.0.JPG',
    'breadboard.jpg': 'https://upload.wikimedia.org/wikipedia/commons/7/73/400_points_breadboard.jpg',
    'jumper_wires.jpg': 'https://upload.wikimedia.org/wikipedia/commons/9/97/F-F_jumper_wires.jpg',
    'ldr.jpg': 'https://upload.wikimedia.org/wikipedia/commons/3/3f/25mm_light-dependent_resistor_%28LDR%29_%281%29.jpg',
    'buzzer.jpg': 'https://upload.wikimedia.org/wikipedia/commons/6/60/Electronic_component_piezo.jpg',
    'led.jpg': 'https://upload.wikimedia.org/wikipedia/commons/4/41/5mm_Cycling_RGB_LED.jpg',
    'resistor.jpg': 'https://upload.wikimedia.org/wikipedia/commons/e/e3/3_Resistors.jpg',
    'capacitor.jpg': 'https://upload.wikimedia.org/wikipedia/commons/a/a4/Aluminium_Electrolytic_Capacitors.jpg',
    'dht11.jpg': 'https://upload.wikimedia.org/wikipedia/commons/c/c3/Dht11_term_and_humidity_sensor.jpg',
    'pir_sensor.jpg': 'https://upload.wikimedia.org/wikipedia/commons/8/85/PIR-inexpensive.jpg',
    'oled_display.jpg': 'https://upload.wikimedia.org/wikipedia/commons/d/df/OLED_Displays.jpg',
    'dc_motor.jpg': 'https://upload.wikimedia.org/wikipedia/commons/e/eb/Dc_motors.jpg',
    'motor_driver.jpg': 'https://upload.wikimedia.org/wikipedia/commons/1/18/Dosmotorsl298n.jpg',
    'battery_holder.jpg': 'https://upload.wikimedia.org/wikipedia/commons/5/56/6x_AA_battery_holder_with_DC_plug.jpg',
    'lcd_display.jpg': 'https://upload.wikimedia.org/wikipedia/commons/a/a1/HD44780.jpg'
}

def download_file(filename, url):
    dest = os.path.join(OUTPUT_DIR, filename)
    print(f"Downloading {filename}...")
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20) as response:
                with open(dest, 'wb') as out_f:
                    out_f.write(response.read())
            size = os.path.getsize(dest)
            print(f"  ✓ Saved {filename} ({size:,} bytes)")
            return True
        except Exception as e:
            print(f"  Attempt {attempt+1} failed for {filename}: {e}")
            time.sleep(3.0 + attempt * 2.0)
    return False

success_count = 0
for filename, url in DOWNLOAD_MAP.items():
    if download_file(filename, url):
        success_count += 1
    time.sleep(1.2)

print(f"\nSuccessfully downloaded {success_count}/{len(DOWNLOAD_MAP)} real hardware photos.")

# Category fallbacks
category_copies = {
    'cat_microcontroller.jpg': 'arduino_nano.jpg',
    'cat_sensor.jpg': 'ultrasonic_sensor.jpg',
    'cat_motor.jpg': 'servo_motor.jpg',
    'cat_display.jpg': 'oled_display.jpg',
    'cat_power.jpg': 'relay_module.jpg',
    'cat_communication.jpg': 'esp8266.jpg',
    'cat_cable.jpg': 'jumper_wires.jpg',
    'cat_pcb.jpg': 'breadboard.jpg',
    'cat_other.jpg': 'resistor.jpg',
    'default.jpg': 'arduino_uno.jpg',
    'ir_sensor.jpg': 'dht11.jpg'
}

for dest_name, src_name in category_copies.items():
    src_path = os.path.join(OUTPUT_DIR, src_name)
    dest_path = os.path.join(OUTPUT_DIR, dest_name)
    if os.path.exists(src_path):
        shutil.copyfile(src_path, dest_path)
        print(f"Created fallback copy: {dest_name} from {src_name}")
