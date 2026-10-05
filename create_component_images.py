"""
Generate clean, professional, high-resolution SVG hardware product visuals
for SECONDLIFE component marketplace.
Consistent style: light studio backdrop, centered hardware, realistic materials,
metallic accents, and clean contrast.
"""

import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'static', 'images', 'components')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def wrap_svg(inner_content, width=320, height=240):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">
  <defs>
    <radialGradient id="bgGrad" cx="50%" cy="45%" r="65%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="70%" stop-color="#f8fafc"/>
      <stop offset="100%" stop-color="#f1f5f9"/>
    </radialGradient>
    <filter id="softShadow" x="-10%" y="-10%" width="130%" height="130%">
      <feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="#0f172a" flood-opacity="0.12"/>
    </filter>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
    <linearGradient id="silverMetal" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="40%" stop-color="#e2e8f0"/>
      <stop offset="70%" stop-color="#94a3b8"/>
      <stop offset="100%" stop-color="#64748b"/>
    </linearGradient>
    <linearGradient id="goldPin" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#fef08a"/>
      <stop offset="50%" stop-color="#eab308"/>
      <stop offset="100%" stop-color="#ca8a04"/>
    </linearGradient>
  </defs>
  <!-- Studio Backdrop -->
  <rect width="{width}" height="{height}" fill="url(#bgGrad)" rx="16"/>
  <!-- Hardware Subject -->
  <g filter="url(#softShadow)">
    {inner_content}
  </g>
</svg>'''

# 1. Ultrasonic Sensor (HC-SR04)
ultrasonic_svg = wrap_svg('''
  <!-- Teal PCB -->
  <rect x="70" y="75" width="180" height="90" rx="6" fill="#0d9488" stroke="#042f2e" stroke-width="1.5"/>
  <rect x="74" y="79" width="172" height="82" rx="4" fill="none" stroke="#2dd4bf" stroke-width="0.75" stroke-dasharray="3,3"/>
  <!-- Crystal Oscillator -->
  <rect x="145" y="112" width="30" height="16" rx="4" fill="url(#silverMetal)" stroke="#64748b"/>
  <!-- Transducer Left (TX) -->
  <circle cx="115" cy="120" r="32" fill="#cbd5e1" stroke="#475569" stroke-width="2"/>
  <circle cx="115" cy="120" r="28" fill="url(#silverMetal)"/>
  <circle cx="115" cy="120" r="23" fill="#1e293b"/>
  <circle cx="115" cy="120" r="20" fill="#0f172a" stroke="#64748b" stroke-width="1" stroke-dasharray="2,2"/>
  <text x="115" y="124" font-size="10" font-family="sans-serif" font-weight="bold" fill="#94a3b8" text-anchor="middle">T</text>
  <!-- Transducer Right (RX) -->
  <circle cx="205" cy="120" r="32" fill="#cbd5e1" stroke="#475569" stroke-width="2"/>
  <circle cx="205" cy="120" r="28" fill="url(#silverMetal)"/>
  <circle cx="205" cy="120" r="23" fill="#1e293b"/>
  <circle cx="205" cy="120" r="20" fill="#0f172a" stroke="#64748b" stroke-width="1" stroke-dasharray="2,2"/>
  <text x="205" y="124" font-size="10" font-family="sans-serif" font-weight="bold" fill="#94a3b8" text-anchor="middle">R</text>
  <!-- 4 Header Pins at bottom -->
  <rect x="135" y="165" width="50" height="8" rx="2" fill="#1e293b"/>
  <line x1="140" y1="173" x2="140" y2="188" stroke="url(#goldPin)" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="150" y1="173" x2="150" y2="188" stroke="url(#goldPin)" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="160" y1="173" x2="160" y2="188" stroke="url(#goldPin)" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="170" y1="173" x2="170" y2="188" stroke="url(#goldPin)" stroke-width="2.5" stroke-linecap="round"/>
  <text x="160" y="93" font-size="9" font-family="sans-serif" font-weight="bold" fill="#f0fdfa" text-anchor="middle" letter-spacing="1">HC-SR04</text>
''')

# 2. Servo Motor (SG90 Micro Servo)
servo_svg = wrap_svg('''
  <!-- Servo Blue Body -->
  <rect x="110" y="85" width="100" height="95" rx="6" fill="#1d4ed8" stroke="#1e3a8a" stroke-width="2"/>
  <!-- Mounting tabs -->
  <rect x="85" y="112" width="25" height="14" rx="2" fill="#1d4ed8" stroke="#1e3a8a" stroke-width="1.5"/>
  <circle cx="95" cy="119" r="3" fill="#cbd5e1"/>
  <rect x="210" y="112" width="25" height="14" rx="2" fill="#1d4ed8" stroke="#1e3a8a" stroke-width="1.5"/>
  <circle cx="225" cy="119" r="3" fill="#cbd5e1"/>
  <!-- Gear Tower Top -->
  <rect x="120" y="65" width="40" height="20" rx="3" fill="#1e40af"/>
  <!-- Output gear / horn hub -->
  <circle cx="140" cy="65" r="16" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.5"/>
  <circle cx="140" cy="65" r="5" fill="#475569"/>
  <!-- Servo Arm / Horn -->
  <path d="M140,55 L210,48 A8,8 0 0,1 210,64 L140,75 Z" fill="#f8fafc" stroke="#94a3b8" stroke-width="1.5"/>
  <circle cx="160" cy="59" r="2.5" fill="#64748b"/>
  <circle cx="180" cy="57" r="2.5" fill="#64748b"/>
  <circle cx="200" cy="55" r="2.5" fill="#64748b"/>
  <!-- Label -->
  <rect x="120" y="125" width="80" height="30" rx="3" fill="#2563eb" stroke="#3b82f6"/>
  <text x="160" y="144" font-size="11" font-family="sans-serif" font-weight="bold" fill="#ffffff" text-anchor="middle" letter-spacing="1">Micro 9g</text>
  <!-- Wire Ribbon out bottom -->
  <path d="M125,180 C125,205 100,210 75,200" fill="none" stroke="#78350f" stroke-width="3" stroke-linecap="round"/>
  <path d="M130,180 C130,208 105,213 80,203" fill="none" stroke="#dc2626" stroke-width="3" stroke-linecap="round"/>
  <path d="M135,180 C135,211 110,216 85,206" fill="none" stroke="#f59e0b" stroke-width="3" stroke-linecap="round"/>
''')

# 3. Jumper Wires (Rainbow Dupont Ribbon)
jumper_wires_svg = wrap_svg('''
  <!-- Multi-color Ribbon Loops -->
  <g fill="none" stroke-width="4.5" stroke-linecap="round">
    <path d="M85,150 C70,70 140,40 180,90 C210,130 240,140 245,150" stroke="#ef4444"/>
    <path d="M80,150 C65,70 135,35 175,85 C205,125 235,135 240,150" stroke="#f97316"/>
    <path d="M75,150 C60,70 130,30 170,80 C200,120 230,130 235,150" stroke="#eab308"/>
    <path d="M70,150 C55,70 125,25 165,75 C195,115 225,125 230,150" stroke="#22c55e"/>
    <path d="M65,150 C50,70 120,20 160,70 C190,110 220,120 225,150" stroke="#06b6d4"/>
    <path d="M60,150 C45,70 115,15 155,65 C185,105 215,115 220,150" stroke="#3b82f6"/>
    <path d="M55,150 C40,70 110,10 150,60 C180,100 210,110 215,150" stroke="#a855f7"/>
  </g>
  <!-- Connector Plugs Left -->
  <g fill="#1e293b" stroke="#0f172a" stroke-width="1">
    <rect x="50" y="150" width="38" height="24" rx="3"/>
    <line x1="56" y1="174" x2="56" y2="194" stroke="url(#silverMetal)" stroke-width="2.5" stroke-linecap="round"/>
    <line x1="63" y1="174" x2="63" y2="194" stroke="url(#silverMetal)" stroke-width="2.5" stroke-linecap="round"/>
    <line x1="70" y1="174" x2="70" y2="194" stroke="url(#silverMetal)" stroke-width="2.5" stroke-linecap="round"/>
    <line x1="77" y1="174" x2="77" y2="194" stroke="url(#silverMetal)" stroke-width="2.5" stroke-linecap="round"/>
    <line x1="84" y1="174" x2="84" y2="194" stroke="url(#silverMetal)" stroke-width="2.5" stroke-linecap="round"/>
  </g>
  <!-- Connector Plugs Right -->
  <g fill="#1e293b" stroke="#0f172a" stroke-width="1">
    <rect x="212" y="150" width="38" height="24" rx="3"/>
    <line x1="218" y1="174" x2="218" y2="194" stroke="url(#silverMetal)" stroke-width="2.5" stroke-linecap="round"/>
    <line x1="225" y1="174" x2="225" y2="194" stroke="url(#silverMetal)" stroke-width="2.5" stroke-linecap="round"/>
    <line x1="232" y1="174" x2="232" y2="194" stroke="url(#silverMetal)" stroke-width="2.5" stroke-linecap="round"/>
    <line x1="239" y1="174" x2="239" y2="194" stroke="url(#silverMetal)" stroke-width="2.5" stroke-linecap="round"/>
    <line x1="246" y1="174" x2="246" y2="194" stroke="url(#silverMetal)" stroke-width="2.5" stroke-linecap="round"/>
  </g>
''')

# 4. Relay Module (5V Single/Dual Channel Relay)
relay_svg = wrap_svg('''
  <!-- Blue PCB base -->
  <rect x="80" y="65" width="160" height="115" rx="8" fill="#1e3a8a" stroke="#172554" stroke-width="2"/>
  <!-- Blue Songle Relay Box -->
  <rect x="115" y="80" width="85" height="60" rx="4" fill="#0284c7" stroke="#0369a1" stroke-width="2"/>
  <rect x="120" y="85" width="75" height="16" fill="#0369a1" rx="2"/>
  <text x="157" y="97" font-size="10" font-family="sans-serif" font-weight="bold" fill="#ffffff" text-anchor="middle">SONGLE</text>
  <text x="157" y="115" font-size="7" font-family="sans-serif" fill="#e0f2fe" text-anchor="middle">10A 250VAC</text>
  <text x="157" y="126" font-size="7" font-family="sans-serif" font-weight="bold" fill="#facc15" text-anchor="middle">SRD-05VDC-SL-C</text>
  <!-- Terminal block on right (Green 3-pin) -->
  <rect x="205" y="88" width="30" height="44" rx="4" fill="#15803d" stroke="#166534" stroke-width="1.5"/>
  <circle cx="220" cy="98" r="4.5" fill="#f1f5f9" stroke="#94a3b8"/>
  <circle cx="220" cy="110" r="4.5" fill="#f1f5f9" stroke="#94a3b8"/>
  <circle cx="220" cy="122" r="4.5" fill="#f1f5f9" stroke="#94a3b8"/>
  <!-- Status LEDs (Red & Green) -->
  <circle cx="98" cy="95" r="4" fill="#ef4444" filter="url(#glow)"/>
  <circle cx="98" cy="110" r="4" fill="#22c55e" filter="url(#glow)"/>
  <!-- Input pins on left -->
  <rect x="85" y="135" width="22" height="12" rx="2" fill="#0f172a"/>
  <line x1="88" y1="147" x2="88" y2="160" stroke="url(#goldPin)" stroke-width="2"/>
  <line x1="94" y1="147" x2="94" y2="160" stroke="url(#goldPin)" stroke-width="2"/>
  <line x1="100" y1="147" x2="100" y2="160" stroke="url(#goldPin)" stroke-width="2"/>
''')

# 5. ESP32 / ESP8266 Dev Board
esp32_svg = wrap_svg('''
  <!-- Black PCB Dev Board -->
  <rect x="95" y="45" width="130" height="155" rx="6" fill="#1e293b" stroke="#0f172a" stroke-width="2"/>
  <!-- Golden PCB Antenna Traces at Top -->
  <rect x="110" y="52" width="100" height="24" rx="3" fill="#0f172a"/>
  <path d="M120,68 L120,58 L135,58 L135,68 L150,68 L150,58 L165,58 L165,68 L180,68 L180,58 L195,58 L195,68" fill="none" stroke="url(#goldPin)" stroke-width="2"/>
  <!-- Metal Shielding Can -->
  <rect x="115" y="85" width="90" height="70" rx="4" fill="url(#silverMetal)" stroke="#64748b" stroke-width="1.5"/>
  <text x="160" y="115" font-size="12" font-family="sans-serif" font-weight="bold" fill="#334155" text-anchor="middle" letter-spacing="1">ESP-WROOM-32</text>
  <text x="160" y="130" font-size="8" font-family="sans-serif" fill="#64748b" text-anchor="middle">WiFi + BT</text>
  <!-- Micro USB Port at bottom -->
  <rect x="145" y="190" width="30" height="14" rx="2" fill="url(#silverMetal)" stroke="#64748b"/>
  <!-- Dual Header Pin Banks on left & right -->
  <g stroke="url(#goldPin)" stroke-width="2.2" stroke-linecap="round">
    <!-- Left pins -->
    <line x1="90" y1="70" x2="98" y2="70"/><line x1="90" y1="80" x2="98" y2="80"/>
    <line x1="90" y1="90" x2="98" y2="90"/><line x1="90" y1="100" x2="98" y2="100"/>
    <line x1="90" y1="110" x2="98" y2="110"/><line x1="90" y1="120" x2="98" y2="120"/>
    <line x1="90" y1="130" x2="98" y2="130"/><line x1="90" y1="140" x2="98" y2="140"/>
    <line x1="90" y1="150" x2="98" y2="150"/><line x1="90" y1="160" x2="98" y2="160"/>
    <line x1="90" y1="170" x2="98" y2="170"/>
    <!-- Right pins -->
    <line x1="222" y1="70" x2="230" y2="70"/><line x1="222" y1="80" x2="230" y2="80"/>
    <line x1="222" y1="90" x2="230" y2="90"/><line x1="222" y1="100" x2="230" y2="100"/>
    <line x1="222" y1="110" x2="230" y2="110"/><line x1="222" y1="120" x2="230" y2="120"/>
    <line x1="222" y1="130" x2="230" y2="130"/><line x1="222" y1="140" x2="230" y2="140"/>
    <line x1="222" y1="150" x2="230" y2="150"/><line x1="222" y1="160" x2="230" y2="160"/>
    <line x1="222" y1="170" x2="230" y2="170"/>
  </g>
''')

# 6. OLED Display Module (0.96" I2C)
oled_svg = wrap_svg('''
  <!-- Blue PCB Base -->
  <rect x="85" y="55" width="150" height="135" rx="8" fill="#0284c7" stroke="#0369a1" stroke-width="2"/>
  <!-- Top 4 Header Pins -->
  <rect x="120" y="47" width="80" height="12" rx="2" fill="#0f172a"/>
  <text x="160" y="66" font-size="7" font-family="sans-serif" font-weight="bold" fill="#ffffff" text-anchor="middle">GND  VCC  SCL  SDA</text>
  <!-- Glossy Black OLED Screen -->
  <rect x="100" y="75" width="120" height="95" rx="4" fill="#020617" stroke="#334155" stroke-width="2"/>
  <!-- Telemetry Graphic on Screen (Glowing Cyan) -->
  <text x="108" y="94" font-size="9" font-family="monospace" font-weight="bold" fill="#38bdf8" filter="url(#glow)">SECONDLIFE v2.0</text>
  <line x1="108" y1="100" x2="212" y2="100" stroke="#0284c7" stroke-width="1"/>
  <!-- Mini waveform graph -->
  <path d="M108,125 L125,125 L135,110 L145,140 L155,115 L165,130 L175,125 L212,125" fill="none" stroke="#22d3ee" stroke-width="1.8" filter="url(#glow)"/>
  <text x="108" y="155" font-size="8" font-family="monospace" fill="#a7f3d0">TEMP: 24.5C OK</text>
''')

# 7. LCD Display Module (16x2 I2C / Parallel)
lcd_svg = wrap_svg('''
  <!-- Green PCB -->
  <rect x="50" y="65" width="220" height="110" rx="6" fill="#15803d" stroke="#166534" stroke-width="2"/>
  <!-- Top Header Pins -->
  <rect x="65" y="58" width="130" height="10" rx="2" fill="#0f172a"/>
  <!-- Metallic Black Screen Bezel -->
  <rect x="70" y="75" width="180" height="85" rx="4" fill="#0f172a" stroke="#334155" stroke-width="2"/>
  <!-- Blue LCD Backlit Area -->
  <rect x="80" y="85" width="160" height="65" rx="3" fill="#0284c7"/>
  <!-- 2x16 Character Grid Text -->
  <text x="90" y="112" font-size="12" font-family="monospace" font-weight="bold" fill="#ffffff" letter-spacing="1.5">SECONDLIFE ECO</text>
  <text x="90" y="134" font-size="12" font-family="monospace" font-weight="bold" fill="#ffffff" letter-spacing="1.5">REUSE: 197g OK!</text>
''')

# 8. DC Motor (Standard Hobby Toy Motor)
dc_motor_svg = wrap_svg('''
  <!-- Cylindrical Metallic Motor Body -->
  <rect x="90" y="90" width="120" height="70" rx="10" fill="url(#silverMetal)" stroke="#64748b" stroke-width="2"/>
  <!-- Back plastic cap -->
  <path d="M90,95 L75,105 L75,145 L90,155 Z" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.5"/>
  <!-- Output metal shaft -->
  <rect x="210" y="120" width="35" height="10" rx="2" fill="url(#silverMetal)" stroke="#475569" stroke-width="1.5"/>
  <!-- Shaft flat groove -->
  <line x1="225" y1="120" x2="245" y2="120" stroke="#334155" stroke-width="1.5"/>
  <!-- Power wires from back -->
  <path d="M75,115 C55,115 50,140 35,145" fill="none" stroke="#ef4444" stroke-width="3" stroke-linecap="round"/>
  <path d="M75,135 C55,135 50,160 35,165" fill="none" stroke="#0f172a" stroke-width="3" stroke-linecap="round"/>
  <!-- Vent slots on metal casing -->
  <rect x="120" y="110" width="10" height="30" rx="2" fill="#475569"/>
  <rect x="145" y="110" width="10" height="30" rx="2" fill="#475569"/>
  <rect x="170" y="110" width="10" height="30" rx="2" fill="#475569"/>
''')

# 9. Motor Driver (L298N)
motor_driver_svg = wrap_svg('''
  <!-- Red PCB Base -->
  <rect x="75" y="60" width="170" height="125" rx="8" fill="#dc2626" stroke="#991b1b" stroke-width="2"/>
  <!-- Big Black Aluminum Heatsink -->
  <rect x="110" y="70" width="100" height="55" rx="4" fill="#1e293b" stroke="#0f172a" stroke-width="1.5"/>
  <line x1="125" y1="70" x2="125" y2="125" stroke="#334155" stroke-width="2"/>
  <line x1="140" y1="70" x2="140" y2="125" stroke="#334155" stroke-width="2"/>
  <line x1="155" y1="70" x2="155" y2="125" stroke="#334155" stroke-width="2"/>
  <line x1="170" y1="70" x2="170" y2="125" stroke="#334155" stroke-width="2"/>
  <line x1="185" y1="70" x2="185" y2="125" stroke="#334155" stroke-width="2"/>
  <line x1="200" y1="70" x2="200" y2="125" stroke="#334155" stroke-width="2"/>
  <!-- Blue Screw Terminals (Left, Right, Bottom) -->
  <rect x="80" y="100" width="22" height="36" rx="3" fill="#0284c7" stroke="#0369a1"/>
  <rect x="218" y="100" width="22" height="36" rx="3" fill="#0284c7" stroke="#0369a1"/>
  <rect x="135" y="145" width="50" height="22" rx="3" fill="#0284c7" stroke="#0369a1"/>
  <!-- Large Filter Capacitor -->
  <circle cx="100" cy="80" r="12" fill="#1e3a8a" stroke="#cbd5e1" stroke-width="2"/>
  <!-- White text label -->
  <text x="160" y="137" font-size="9" font-family="sans-serif" font-weight="bold" fill="#ffffff" text-anchor="middle">L298N DUAL H-BRIDGE</text>
''')

# 10. Breadboard (White Solderless Breadboard)
breadboard_svg = wrap_svg('''
  <!-- Breadboard Body -->
  <rect x="40" y="60" width="240" height="120" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="2"/>
  <!-- Center Divider Trench -->
  <line x1="45" y1="120" x2="275" y2="120" stroke="#94a3b8" stroke-width="2.5"/>
  <!-- Top Power Rails (+ / -) -->
  <line x1="50" y1="72" x2="270" y2="72" stroke="#ef4444" stroke-width="1.8"/>
  <line x1="50" y1="80" x2="270" y2="80" stroke="#3b82f6" stroke-width="1.8"/>
  <!-- Bottom Power Rails (+ / -) -->
  <line x1="50" y1="160" x2="270" y2="160" stroke="#ef4444" stroke-width="1.8"/>
  <line x1="50" y1="168" x2="270" y2="168" stroke="#3b82f6" stroke-width="1.8"/>
  <!-- Grid Matrix of Tie Points -->
  <g fill="#475569">
    <!-- Row pattern across width -->
    ''' + "".join([f'<rect x="{60 + i*14}" y="92" width="4" height="4" rx="0.5"/><rect x="{60 + i*14}" y="102" width="4" height="4" rx="0.5"/><rect x="{60 + i*14}" y="134" width="4" height="4" rx="0.5"/><rect x="{60 + i*14}" y="144" width="4" height="4" rx="0.5"/>' for i in range(15)]) + '''
  </g>
''')

# 11. Battery Holder / Pack
battery_svg = wrap_svg('''
  <!-- Black Battery Casing -->
  <rect x="75" y="80" width="170" height="85" rx="8" fill="#1e293b" stroke="#0f172a" stroke-width="2"/>
  <!-- Cell 1 -->
  <rect x="85" y="90" width="70" height="65" rx="6" fill="#334155"/>
  <rect x="90" y="98" width="55" height="49" rx="4" fill="#0284c7"/>
  <text x="117" y="128" font-size="11" font-family="sans-serif" font-weight="bold" fill="#ffffff" text-anchor="middle">AA 1.5V</text>
  <!-- Cell 2 -->
  <rect x="165" y="90" width="70" height="65" rx="6" fill="#334155"/>
  <rect x="170" y="98" width="55" height="49" rx="4" fill="#0284c7"/>
  <text x="197" y="128" font-size="11" font-family="sans-serif" font-weight="bold" fill="#ffffff" text-anchor="middle">AA 1.5V</text>
  <!-- Positive/Negative Lead Wires -->
  <path d="M245,100 C270,100 275,130 290,135" fill="none" stroke="#ef4444" stroke-width="3" stroke-linecap="round"/>
  <path d="M245,145 C270,145 275,160 290,165" fill="none" stroke="#0f172a" stroke-width="3" stroke-linecap="round"/>
''')

# 12. Resistor Pack
resistor_svg = wrap_svg('''
  <!-- Group of 3 Resistors with Colored Bands -->
  <!-- Resistor 1: 10K (Brown, Black, Orange, Gold) -->
  <g>
    <line x1="40" y1="80" x2="280" y2="80" stroke="url(#silverMetal)" stroke-width="2.5" stroke-linecap="round"/>
    <rect x="110" y="68" width="100" height="24" rx="10" fill="#fde68a" stroke="#d97706" stroke-width="1.5"/>
    <rect x="130" y="68" width="8" height="24" fill="#78350f"/><!-- Brown -->
    <rect x="146" y="68" width="8" height="24" fill="#0f172a"/><!-- Black -->
    <rect x="162" y="68" width="8" height="24" fill="#ea580c"/><!-- Orange -->
    <rect x="186" y="68" width="6" height="24" fill="#eab308"/><!-- Gold -->
  </g>
  <!-- Resistor 2: 220 Ohm (Red, Red, Brown, Gold) -->
  <g>
    <line x1="40" y1="120" x2="280" y2="120" stroke="url(#silverMetal)" stroke-width="2.5" stroke-linecap="round"/>
    <rect x="110" y="108" width="100" height="24" rx="10" fill="#fde68a" stroke="#d97706" stroke-width="1.5"/>
    <rect x="130" y="108" width="8" height="24" fill="#dc2626"/><!-- Red -->
    <rect x="146" y="108" width="8" height="24" fill="#dc2626"/><!-- Red -->
    <rect x="162" y="108" width="8" height="24" fill="#78350f"/><!-- Brown -->
    <rect x="186" y="108" width="6" height="24" fill="#eab308"/><!-- Gold -->
  </g>
  <!-- Resistor 3: 1K (Brown, Black, Red, Gold) -->
  <g>
    <line x1="40" y1="160" x2="280" y2="160" stroke="url(#silverMetal)" stroke-width="2.5" stroke-linecap="round"/>
    <rect x="110" y="148" width="100" height="24" rx="10" fill="#fde68a" stroke="#d97706" stroke-width="1.5"/>
    <rect x="130" y="148" width="8" height="24" fill="#78350f"/><!-- Brown -->
    <rect x="146" y="148" width="8" height="24" fill="#0f172a"/><!-- Black -->
    <rect x="162" y="148" width="8" height="24" fill="#dc2626"/><!-- Red -->
    <rect x="186" y="148" width="6" height="24" fill="#eab308"/><!-- Gold -->
  </g>
''')

# 13. Capacitor Pack
capacitor_svg = wrap_svg('''
  <!-- Electrolytic Can 1 (Blue) -->
  <rect x="80" y="80" width="55" height="90" rx="8" fill="#1d4ed8" stroke="#1e3a8a" stroke-width="2"/>
  <rect x="85" y="80" width="12" height="90" fill="#f1f5f9"/>
  <text x="91" y="130" font-size="14" font-weight="bold" fill="#0f172a" text-anchor="middle">-</text>
  <text x="115" y="125" font-size="9" font-family="sans-serif" font-weight="bold" fill="#ffffff" text-anchor="middle">100uF</text>
  <line x1="95" y1="170" x2="95" y2="195" stroke="url(#silverMetal)" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="120" y1="170" x2="120" y2="202" stroke="url(#silverMetal)" stroke-width="2.5" stroke-linecap="round"/>
  <!-- Electrolytic Can 2 (Black) -->
  <rect x="155" y="95" width="45" height="75" rx="6" fill="#1e293b" stroke="#0f172a" stroke-width="2"/>
  <rect x="159" y="95" width="10" height="75" fill="#e2e8f0"/>
  <text x="164" y="135" font-size="12" font-weight="bold" fill="#0f172a" text-anchor="middle">-</text>
  <text x="182" y="135" font-size="8" font-family="sans-serif" font-weight="bold" fill="#ffffff" text-anchor="middle">47uF</text>
  <line x1="168" y1="170" x2="168" y2="192" stroke="url(#silverMetal)" stroke-width="2" stroke-linecap="round"/>
  <line x1="188" y1="170" x2="188" y2="198" stroke="url(#silverMetal)" stroke-width="2" stroke-linecap="round"/>
  <!-- Ceramic Disc Capacitors (Orange) -->
  <circle cx="230" cy="115" r="18" fill="#ea580c" stroke="#c2410c" stroke-width="1.5"/>
  <text x="230" y="119" font-size="9" font-family="sans-serif" font-weight="bold" fill="#ffffff" text-anchor="middle">104</text>
  <line x1="224" y1="133" x2="224" y2="175" stroke="url(#silverMetal)" stroke-width="2" stroke-linecap="round"/>
  <line x1="236" y1="133" x2="236" y2="175" stroke="url(#silverMetal)" stroke-width="2" stroke-linecap="round"/>
''')

# 14. DHT11 Temperature & Humidity Sensor
dht11_svg = wrap_svg('''
  <!-- Blue Perforated Housing -->
  <rect x="110" y="70" width="100" height="110" rx="6" fill="#0284c7" stroke="#0369a1" stroke-width="2"/>
  <!-- Wave grid vents -->
  <g fill="#0369a1">
    ''' + "".join([f'<rect x="{125 + j*18}" y="{85 + k*15}" width="10" height="6" rx="2"/>' for j in range(4) for k in range(4)]) + '''
  </g>
  <!-- Label -->
  <text x="160" y="165" font-size="11" font-family="sans-serif" font-weight="bold" fill="#ffffff" text-anchor="middle" letter-spacing="1">DHT11</text>
  <!-- 4 Connector Pins at bottom -->
  <line x1="130" y1="180" x2="130" y2="205" stroke="url(#silverMetal)" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="150" y1="180" x2="150" y2="205" stroke="url(#silverMetal)" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="170" y1="180" x2="170" y2="205" stroke="url(#silverMetal)" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="190" y1="180" x2="190" y2="205" stroke="url(#silverMetal)" stroke-width="2.5" stroke-linecap="round"/>
''')

# 15. PIR Motion Sensor (HC-SR501)
pir_svg = wrap_svg('''
  <!-- Green Base PCB -->
  <rect x="90" y="85" width="140" height="95" rx="6" fill="#15803d" stroke="#166534" stroke-width="2"/>
  <!-- White Faceted Fresnel Dome -->
  <circle cx="160" cy="130" r="42" fill="#ffffff" stroke="#cbd5e1" stroke-width="2"/>
  <circle cx="160" cy="130" r="34" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5"/>
  <circle cx="160" cy="130" r="24" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="1"/>
  <!-- Facet segments -->
  <line x1="160" y1="88" x2="160" y2="172" stroke="#e2e8f0" stroke-width="1"/>
  <line x1="118" y1="130" x2="202" y2="130" stroke="#e2e8f0" stroke-width="1"/>
  <!-- Orange sensitivity potentiometer pots at top corners -->
  <circle cx="108" cy="98" r="7" fill="#ea580c" stroke="#c2410c"/>
  <circle cx="212" cy="98" r="7" fill="#ea580c" stroke="#c2410c"/>
''')

# 16. LED Pack (Assorted Diffused 5mm LEDs)
led_svg = wrap_svg('''
  <!-- Green LED -->
  <g transform="translate(60, 60)">
    <path d="M20,50 L20,30 A15,15 0 0,1 50,30 L50,50 Z" fill="#22c55e" stroke="#16a34a" stroke-width="1.5" filter="url(#glow)"/>
    <rect x="18" y="50" width="34" height="6" rx="1" fill="#16a34a"/>
    <line x1="28" y1="56" x2="28" y2="110" stroke="url(#silverMetal)" stroke-width="2" stroke-linecap="round"/>
    <line x1="42" y1="56" x2="42" y2="120" stroke="url(#silverMetal)" stroke-width="2" stroke-linecap="round"/>
  </g>
  <!-- Red LED -->
  <g transform="translate(125, 60)">
    <path d="M20,50 L20,30 A15,15 0 0,1 50,30 L50,50 Z" fill="#ef4444" stroke="#dc2626" stroke-width="1.5" filter="url(#glow)"/>
    <rect x="18" y="50" width="34" height="6" rx="1" fill="#dc2626"/>
    <line x1="28" y1="56" x2="28" y2="110" stroke="url(#silverMetal)" stroke-width="2" stroke-linecap="round"/>
    <line x1="42" y1="56" x2="42" y2="120" stroke="url(#silverMetal)" stroke-width="2" stroke-linecap="round"/>
  </g>
  <!-- Blue LED -->
  <g transform="translate(190, 60)">
    <path d="M20,50 L20,30 A15,15 0 0,1 50,30 L50,50 Z" fill="#3b82f6" stroke="#2563eb" stroke-width="1.5" filter="url(#glow)"/>
    <rect x="18" y="50" width="34" height="6" rx="1" fill="#2563eb"/>
    <line x1="28" y1="56" x2="28" y2="110" stroke="url(#silverMetal)" stroke-width="2" stroke-linecap="round"/>
    <line x1="42" y1="56" x2="42" y2="120" stroke="url(#silverMetal)" stroke-width="2" stroke-linecap="round"/>
  </g>
''')

# 17. Soil Moisture Sensor Probe
soil_moisture_svg = wrap_svg('''
  <!-- Top module PCB -->
  <rect x="120" y="55" width="80" height="45" rx="4" fill="#1e3a8a" stroke="#172554"/>
  <circle cx="135" cy="72" r="3" fill="#ef4444"/>
  <circle cx="150" cy="72" r="3" fill="#22c55e"/>
  <!-- 2-Prong Fork Probe -->
  <path d="M135,100 L135,185 L145,195 L145,100 Z" fill="url(#goldPin)" stroke="#ca8a04"/>
  <path d="M175,100 L175,185 L185,195 L185,100 Z" fill="url(#goldPin)" stroke="#ca8a04"/>
''')

# 18. Piezo Buzzer
buzzer_svg = wrap_svg('''
  <!-- Round Black Piezo Case -->
  <circle cx="160" cy="115" r="48" fill="#1e293b" stroke="#0f172a" stroke-width="2"/>
  <circle cx="160" cy="115" r="40" fill="#334155"/>
  <!-- Central Sound Emission Hole -->
  <circle cx="160" cy="115" r="9" fill="#0f172a"/>
  <!-- Polarity Positive (+) Marking -->
  <text x="135" y="95" font-size="16" font-family="sans-serif" font-weight="bold" fill="#f87171">+</text>
  <!-- Bottom Pins -->
  <line x1="145" y1="163" x2="145" y2="190" stroke="url(#silverMetal)" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="175" y1="163" x2="175" y2="190" stroke="url(#silverMetal)" stroke-width="2.5" stroke-linecap="round"/>
''')

# 19. Raspberry Pi 3B / SBC
raspberry_pi_svg = wrap_svg('''
  <!-- Green PCB -->
  <rect x="75" y="55" width="170" height="130" rx="8" fill="#15803d" stroke="#166534" stroke-width="2"/>
  <!-- 40-Pin GPIO Header -->
  <rect x="85" y="62" width="125" height="14" rx="2" fill="#0f172a"/>
  <!-- Broadcom SoC Chip -->
  <rect x="130" y="95" width="45" height="45" rx="3" fill="url(#silverMetal)" stroke="#64748b"/>
  <text x="152" y="122" font-size="8" font-family="sans-serif" font-weight="bold" fill="#334155" text-anchor="middle">BROADCOM</text>
  <!-- 4 USB-A Ports (Silver cans on right) -->
  <rect x="220" y="80" width="30" height="32" rx="3" fill="url(#silverMetal)" stroke="#64748b"/>
  <rect x="220" y="120" width="30" height="32" rx="3" fill="url(#silverMetal)" stroke="#64748b"/>
  <!-- Ethernet Port -->
  <rect x="180" y="150" width="32" height="38" rx="3" fill="url(#silverMetal)" stroke="#64748b"/>
  <!-- HDMI Port -->
  <rect x="135" y="172" width="24" height="15" rx="2" fill="url(#silverMetal)"/>
''')

# 20. Arduino Nano
arduino_nano_svg = wrap_svg('''
  <!-- Blue Mini PCB -->
  <rect x="90" y="60" width="140" height="120" rx="6" fill="#0284c7" stroke="#0369a1" stroke-width="2"/>
  <!-- Mini USB at left -->
  <rect x="78" y="105" width="22" height="30" rx="2" fill="url(#silverMetal)" stroke="#64748b"/>
  <!-- ATmega TQFP Square Chip in center -->
  <rect x="145" y="105" width="30" height="30" rx="2" fill="#0f172a" stroke="#334155"/>
  <circle cx="150" cy="110" r="1.5" fill="#f8fafc"/>
  <text x="160" y="95" font-size="10" font-family="sans-serif" font-weight="bold" fill="#ffffff" text-anchor="middle">NANO</text>
  <!-- Top and Bottom Pin Rows -->
  <g stroke="url(#goldPin)" stroke-width="2.2" stroke-linecap="round">
    ''' + "".join([f'<line x1="{105 + i*8}" y1="52" x2="{105 + i*8}" y2="60"/><line x1="{105 + i*8}" y1="180" x2="{105 + i*8}" y2="188"/>' for i in range(15)]) + '''
  </g>
''')

# 21. Water Pump / Submersible Pump
water_pump_svg = wrap_svg('''
  <!-- Black Submersible Body -->
  <rect x="100" y="80" width="105" height="90" rx="10" fill="#1e293b" stroke="#0f172a" stroke-width="2"/>
  <!-- Output Water Spout (Cylinder top) -->
  <rect x="140" y="55" width="24" height="26" rx="3" fill="#334155" stroke="#1e293b"/>
  <!-- Intake Grill on front -->
  <g fill="#0f172a">
    <rect x="110" y="125" width="40" height="5" rx="1"/>
    <rect x="110" y="135" width="40" height="5" rx="1"/>
    <rect x="110" y="145" width="40" height="5" rx="1"/>
  </g>
  <!-- Power Cord (Clear/flexible tube look) -->
  <path d="M205,120 C235,120 240,150 265,155" fill="none" stroke="#ef4444" stroke-width="3" stroke-linecap="round"/>
  <path d="M205,130 C235,130 240,160 265,165" fill="none" stroke="#0f172a" stroke-width="3" stroke-linecap="round"/>
''')

# Category Fallbacks
microcontroller_fallback = arduino_nano_svg
sensor_fallback = ultrasonic_svg
motor_fallback = servo_svg
display_fallback = oled_svg
power_fallback = battery_svg
communication_fallback = esp32_svg
cable_fallback = jumper_wires_svg
pcb_fallback = breadboard_svg
other_fallback = resistor_svg
default_fallback = ultrasonic_svg

assets = {
    'ultrasonic_sensor.svg': ultrasonic_svg,
    'servo_motor.svg': servo_svg,
    'jumper_wires.svg': jumper_wires_svg,
    'relay_module.svg': relay_svg,
    'esp32.svg': esp32_svg,
    'esp8266.svg': esp32_svg,
    'oled_display.svg': oled_svg,
    'lcd_display.svg': lcd_svg,
    'dc_motor.svg': dc_motor_svg,
    'motor_driver.svg': motor_driver_svg,
    'breadboard.svg': breadboard_svg,
    'battery_holder.svg': battery_svg,
    'battery.svg': battery_svg,
    'resistor_pack.svg': resistor_svg,
    'capacitor_pack.svg': capacitor_svg,
    'dht11_sensor.svg': dht11_svg,
    'pir_sensor.svg': pir_svg,
    'ir_sensor.svg': dht11_svg,
    'ldr_sensor.svg': resistor_svg,
    'led_pack.svg': led_svg,
    'soil_moisture_sensor.svg': soil_moisture_svg,
    'buzzer.svg': buzzer_svg,
    'raspberry_pi.svg': raspberry_pi_svg,
    'arduino_nano.svg': arduino_nano_svg,
    'water_pump.svg': water_pump_svg,
    # Category mappings
    'cat_microcontroller.svg': microcontroller_fallback,
    'cat_sensor.svg': sensor_fallback,
    'cat_motor.svg': motor_fallback,
    'cat_display.svg': display_fallback,
    'cat_power.svg': power_fallback,
    'cat_communication.svg': communication_fallback,
    'cat_cable.svg': cable_fallback,
    'cat_pcb.svg': pcb_fallback,
    'cat_other.svg': other_fallback,
    'default.svg': default_fallback
}

for filename, content in assets.items():
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Wrote {filename}')

print(f'Successfully generated {len(assets)} hardware component visuals in {OUTPUT_DIR}')
