from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(f):
    """Decorator to require authentication for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def format_weight(grams):
    """Format weight in grams to a human-readable string."""
    if grams is None or grams == 0:
        return '0 g'
    if grams >= 1000:
        return f'{grams / 1000:.2f} kg'
    return f'{grams:.0f} g'


def format_currency(amount):
    """Format an amount into Indian Rupees format e.g. ₹450, ₹1,200, ₹3,500."""
    if amount is None:
        return '₹0'
    try:
        val = float(amount)
        if val.is_integer():
            s = f"{int(val):,}"
        else:
            s = f"{val:,.2f}"
        return f"₹{s}"
    except (ValueError, TypeError):
        return f"₹{amount}"


ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


def allowed_file(filename):
    """Check if a filename has an allowed image extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def get_component_image(comp):
    """
    Returns the relative path under static/ for the best image of a component.
    1. If comp has an uploaded image (comp.image) and it exists in static/uploads/, return 'uploads/' + comp.image
    2. Fallback to high-quality local hardware visual based on component name keywords
    3. Fallback based on component category
    4. Ultimate fallback to default component visual
    """
    if not comp:
        return 'images/components/default.jpg'

    image = getattr(comp, 'image', None) if not isinstance(comp, dict) else comp.get('image')
    name = (getattr(comp, 'name', '') if not isinstance(comp, dict) else comp.get('name', '')) or ''
    category = (getattr(comp, 'category', '') if not isinstance(comp, dict) else comp.get('category', '')) or ''

    if image:
        if image.startswith('images/') or image.startswith('uploads/'):
            return image
        return f'uploads/{image}'

    name_lower = name.lower()
    cat_lower = category.lower()

    # Exact/keyword match for real hardware components
    if 'arduino uno' in name_lower or 'ardiuno uno' in name_lower:
        return 'images/components/arduino_uno.jpg'
    elif 'arduino nano' in name_lower or 'nano' in name_lower:
        return 'images/components/arduino_nano.jpg'
    elif 'raspberry' in name_lower or 'rpi' in name_lower:
        return 'images/components/raspberry_pi.jpg'
    elif 'esp32' in name_lower:
        return 'images/components/esp32.jpg'
    elif 'esp8266' in name_lower or 'nodemcu' in name_lower or 'wifi' in name_lower:
        return 'images/components/esp8266.jpg'
    elif 'ultrasonic' in name_lower or 'hc-sr04' in name_lower or 'distance' in name_lower:
        return 'images/components/ultrasonic_sensor.jpg'
    elif 'servo' in name_lower or 'sg90' in name_lower or 'mg996' in name_lower:
        return 'images/components/servo_motor.jpg'
    elif 'dc motor' in name_lower or 'gear motor' in name_lower or 'bo motor' in name_lower:
        return 'images/components/dc_motor.jpg'
    elif 'l298n' in name_lower or 'motor driver' in name_lower or 'driver' in name_lower:
        return 'images/components/motor_driver.jpg'
    elif 'pump' in name_lower or 'submersible' in name_lower:
        return 'images/components/water_pump.jpg'
    elif 'relay' in name_lower:
        return 'images/components/relay_module.jpg'
    elif 'jumper' in name_lower or 'dupont' in name_lower or 'wire' in name_lower:
        return 'images/components/jumper_wires.jpg'
    elif 'oled' in name_lower or 'ssd1306' in name_lower:
        return 'images/components/oled_display.jpg'
    elif 'lcd' in name_lower or '16x2' in name_lower or 'i2c lcd' in name_lower:
        return 'images/components/lcd_display.jpg'
    elif 'dht11' in name_lower or 'dht22' in name_lower or 'temp' in name_lower or 'humidity' in name_lower:
        return 'images/components/dht11.jpg'
    elif 'pir' in name_lower or 'motion' in name_lower:
        return 'images/components/pir_sensor.jpg'
    elif 'ir ' in name_lower or 'infrared' in name_lower or name_lower.startswith('ir'):
        return 'images/components/ir_sensor.jpg'
    elif 'ldr' in name_lower or 'photoresistor' in name_lower or 'light' in name_lower:
        return 'images/components/ldr.jpg'
    elif 'soil' in name_lower or 'moisture' in name_lower:
        return 'images/components/soil_moisture_sensor.jpg'
    elif 'breadboard' in name_lower:
        return 'images/components/breadboard.jpg'
    elif 'battery' in name_lower or 'holder' in name_lower or '18650' in name_lower or '9v' in name_lower:
        return 'images/components/battery_holder.jpg'
    elif 'resistor' in name_lower:
        return 'images/components/resistor.jpg'
    elif 'capacitor' in name_lower:
        return 'images/components/capacitor.jpg'
    elif 'buzzer' in name_lower or 'piezo' in name_lower or 'sound' in name_lower:
        return 'images/components/buzzer.jpg'
    elif 'led' in name_lower:
        return 'images/components/led.jpg'

    # Category fallback
    if 'microcontroller' in cat_lower or 'development' in cat_lower:
        return 'images/components/cat_microcontroller.jpg'
    elif 'sensor' in cat_lower:
        return 'images/components/cat_sensor.jpg'
    elif 'motor' in cat_lower or 'actuator' in cat_lower:
        return 'images/components/cat_motor.jpg'
    elif 'display' in cat_lower or 'screen' in cat_lower:
        return 'images/components/cat_display.jpg'
    elif 'power' in cat_lower or 'battery' in cat_lower:
        return 'images/components/cat_power.jpg'
    elif 'comm' in cat_lower or 'wireless' in cat_lower:
        return 'images/components/cat_communication.jpg'
    elif 'cable' in cat_lower or 'wire' in cat_lower:
        return 'images/components/cat_cable.jpg'
    elif 'pcb' in cat_lower or 'board' in cat_lower:
        return 'images/components/cat_pcb.jpg'
    elif 'passive' in cat_lower or 'component' in cat_lower:
        return 'images/components/cat_other.jpg'

    return 'images/components/default.jpg'


def get_project_image(project):
    """
    Returns the relative path under static/ for the best image of a project.
    1. If project has an uploaded image (project.image) and exists or is valid, return it
    2. Fallback to specific real local project photograph in static/images/projects/
    3. Fallback based on project category to a real category photo
    4. Ultimate fallback to default maker workbench photograph (never generic icons)
    """
    if not project:
        return 'images/projects/default.jpg'

    image = getattr(project, 'image', None) if not isinstance(project, dict) else project.get('image')
    title = (getattr(project, 'title', '') if not isinstance(project, dict) else project.get('title', '')) or ''
    category = (getattr(project, 'category', '') if not isinstance(project, dict) else project.get('category', '')) or ''

    if image:
        if image.startswith('images/') or image.startswith('uploads/'):
            return image
        return f'uploads/{image}'

    title_lower = title.lower()
    cat_lower = category.lower()

    # Exact / keyword match for real project photographs
    if 'dustbin' in title_lower or 'trash' in title_lower:
        return 'images/projects/smart-dustbin.jpg'
    elif 'plant' in title_lower or 'watering' in title_lower:
        return 'images/projects/automatic-plant-watering.jpg'
    elif 'parking' in title_lower:
        return 'images/projects/smart-parking-system.jpg'
    elif 'line' in title_lower and ('follow' in title_lower or 'robot' in title_lower):
        return 'images/projects/line-following-robot.jpg'
    elif 'obstacle' in title_lower or 'avoiding' in title_lower:
        return 'images/projects/obstacle-avoiding-robot.jpg'
    elif 'home' in title_lower and 'automation' in title_lower:
        return 'images/projects/home-automation-system.jpg'
    elif 'weather' in title_lower:
        return 'images/projects/weather-monitoring-station.jpg'
    elif 'door' in title_lower or 'lock' in title_lower:
        return 'images/projects/smart-door-lock.jpg'
    elif 'alarm' in title_lower or 'security' in title_lower:
        return 'images/projects/mini-security-alarm.jpg'
    elif 'night' in title_lower or 'lamp' in title_lower:
        return 'images/projects/automatic-night-lamp.jpg'
    elif 'temperature' in title_lower or 'digital temp' in title_lower:
        return 'images/projects/digital-temperature-monitor.jpg'
    elif 'environment' in title_lower or 'env' in title_lower:
        return 'images/projects/iot-environment-monitor.jpg'

    # Category fallback using authentic project photos
    if 'robot' in cat_lower:
        return 'images/projects/obstacle-avoiding-robot.jpg'
    elif 'smart' in cat_lower or 'home' in cat_lower:
        return 'images/projects/home-automation-system.jpg'
    elif 'iot' in cat_lower:
        return 'images/projects/iot-environment-monitor.jpg'
    elif 'auto' in cat_lower:
        return 'images/projects/automatic-plant-watering.jpg'
    elif 'edu' in cat_lower:
        return 'images/projects/digital-temperature-monitor.jpg'
    elif 'elec' in cat_lower:
        return 'images/projects/automatic-night-lamp.jpg'

    return 'images/projects/default.jpg'

