import urllib.request
import json
import time

items = [
    ('soil_moisture', 'soil moisture sensor'),
    ('water_pump', 'submersible pump'),
    ('dc_motor', 'gearmotor'),
    ('dc_motor2', 'electric motor hobby'),
    ('oled', 'OLED display'),
    ('l298n', 'motor driver H bridge'),
    ('battery_holder', 'battery holder'),
    ('ir_sensor', 'infrared obstacle sensor'),
    ('ir_sensor2', 'phototransistor')
]

for name, query in items:
    time.sleep(1.0)
    url = f'https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={urllib.parse.quote(query)}&gsrnamespace=6&prop=imageinfo&iiprop=url|mime|size&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': 'SecondLifeEdu/1.0 (contact: pradeep@secondlife.local)'})
    try:
        res = urllib.request.urlopen(req, timeout=10)
        data = json.loads(res.read())
        pages = data.get('query', {}).get('pages', {})
        print(f"=== {name} ({query}) ===")
        found = 0
        for pid, p in pages.items():
            t = p.get('title', '').encode('ascii', 'replace').decode('ascii')
            info = p.get('imageinfo', [{}])[0]
            m = info.get('mime', '')
            u = info.get('url', '')
            if m.startswith('image/') and not m.endswith('svg+xml') and not m.endswith('gif'):
                print(f"  {t} -> {u}")
                found += 1
                if found >= 4:
                    break
    except Exception as e:
        print(f"Error {name}: {e}")
