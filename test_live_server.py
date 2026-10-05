"""
Live Server HTTP Integration Test for SECONDLIFE
Performs live HTTP requests against http://127.0.0.1:5000 to verify:
- Network connectivity and responses
- Static assets (CSS, JS)
- Authentication session management
- Public routes and query parameters (search, filter)
- Protected user routes (dashboard, matches, saved projects, profile)
- Role-based authorization on admin routes
- Custom 404 error handling
"""

import sys
import os
import urllib.request
import urllib.parse
import http.cookiejar

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = 'http://127.0.0.1:5000'


class LiveClient:
    def __init__(self):
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar),
            urllib.request.HTTPRedirectHandler()
        )

    def get(self, path):
        url = BASE_URL + path if path.startswith('/') else path
        req = urllib.request.Request(url, headers={'User-Agent': 'SECONDLIFE-TestClient'})
        try:
            with self.opener.open(req) as res:
                return res.getcode(), res.read().decode('utf-8', errors='replace'), res.geturl()
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode('utf-8', errors='replace'), e.geturl()

    def post(self, path, data):
        url = BASE_URL + path if path.startswith('/') else path
        encoded = urllib.parse.urlencode(data).encode('utf-8')
        req = urllib.request.Request(url, data=encoded, headers={
            'User-Agent': 'SECONDLIFE-TestClient',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        try:
            with self.opener.open(req) as res:
                return res.getcode(), res.read().decode('utf-8', errors='replace'), res.geturl()
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode('utf-8', errors='replace'), e.geturl()


def run_live_tests():
    print("=" * 70)
    print("RUNNING LIVE HTTP INTEGRATION TESTS AGAINST " + BASE_URL)
    print("=" * 70)

    client = LiveClient()

    # 1. Home page
    print("\n[1] Testing Homepage (GET /)...")
    status, html, final_url = client.get('/')
    assert status == 200, f"Expected 200, got {status}"
    assert "SECONDLIFE" in html
    assert "Give Your Electronics" in html
    print("  ✓ Homepage responded with 200 OK and expected branding")

    # 2. Static CSS & JS Assets
    print("\n[2] Testing Static Assets...")
    status, css, _ = client.get('/static/css/style.css')
    assert status == 200, f"CSS load failed: {status}"
    assert "--primary" in css or "--eco-green" in css
    print("  ✓ /static/css/style.css loaded successfully (200 OK)")

    status, js, _ = client.get('/static/js/app.js')
    assert status == 200, f"JS load failed: {status}"
    assert "DOMContentLoaded" in js
    print("  ✓ /static/js/app.js loaded successfully (200 OK)")

    # 3. Public Components Listing with Search & Filters
    print("\n[3] Testing Public Components with Search & Filters...")
    status, html, _ = client.get('/components')
    assert status == 200
    assert "Electronic Components" in html
    print("  ✓ /components returned 200 OK")

    # Filter by category
    status, html, _ = client.get('/components?category=Microcontroller')
    assert status == 200
    assert "Arduino" in html
    print("  ✓ /components?category=Microcontroller correctly filters results")

    # Search by keyword
    status, html, _ = client.get('/components?search=Sensor')
    assert status == 200
    assert "Sensor" in html
    print("  ✓ /components?search=Sensor correctly returns matching components")

    # 4. Public Projects Listing & Details
    print("\n[4] Testing Public Projects Listing & Details...")
    status, html, _ = client.get('/projects')
    assert status == 200
    assert "Reuse Projects" in html
    assert "Smart Dustbin" in html
    print("  ✓ /projects loaded with reuse projects")

    status, html, _ = client.get('/projects/1')
    assert status == 200
    assert "Smart Dustbin" in html
    assert "Required Components" in html
    print("  ✓ /projects/1 details page loaded with requirements table")

    # 5. User Authentication (Login as Rahul)
    print("\n[5] Testing User Authentication & Session...")
    status, html, final_url = client.post('/login', {
        'email': 'rahul@example.com',
        'password': 'password123'
    })
    assert status == 200
    assert "Dashboard" in html or "Rahul" in html
    print("  ✓ Logged in as rahul@example.com, redirected to Dashboard")

    # 6. User Dashboard (Authenticated)
    print("\n[6] Testing User Dashboard...")
    status, html, _ = client.get('/dashboard')
    assert status == 200
    assert "Dashboard" in html
    assert "My Components" in html
    assert "E-Waste Diverted" in html
    assert "categoryChart" in html
    print("  ✓ Dashboard rendered with stat cards and Chart.js integration")

    # 7. Matches Page
    print("\n[7] Testing Smart Matches Page (/matches)...")
    status, html, _ = client.get('/matches')
    assert status == 200
    assert "Smart Project Matches" in html
    assert "%" in html
    print("  ✓ Matches page rendered with feasibility percentages")

    # 8. Saved Projects Page
    print("\n[8] Testing Saved Projects Page (/saved-projects)...")
    status, html, _ = client.get('/saved-projects')
    assert status == 200
    assert "Saved Projects" in html
    print("  ✓ Saved Projects page rendered")

    # 9. User Profile Page
    print("\n[9] Testing Profile Page (/profile)...")
    status, html, _ = client.get('/profile')
    assert status == 200
    assert "Rahul Sharma" in html
    assert "Account Settings" in html
    print("  ✓ Profile page rendered with user details")

    # 10. Role-Based Access Control: Regular user cannot access Admin
    print("\n[10] Testing Admin Route Protection for Regular Users...")
    status, html, final_url = client.get('/admin/')
    assert "Admin privileges required" in html or "/dashboard" in final_url
    print("  ✓ Regular user blocked from /admin/, redirected to Dashboard")

    # 11. Logout
    print("\n[11] Testing Logout...")
    status, html, _ = client.get('/logout')
    assert status == 200
    assert "logged out" in html
    print("  ✓ Logged out successfully")

    # 12. Admin Login & Admin Dashboard
    print("\n[12] Testing Admin Login & Dashboard...")
    status, html, _ = client.post('/login', {
        'email': 'admin@secondlife.com',
        'password': 'admin123'
    })
    assert status == 200
    assert "Admin Dashboard" in html

    status, html, _ = client.get('/admin/')
    assert status == 200
    assert "Total Users" in html
    assert "Components" in html
    assert "adminCategoryChart" in html
    print("  ✓ Admin logged in and Admin Dashboard loaded with Chart.js analytics")

    # Admin subpages
    status, html, _ = client.get('/admin/users')
    assert status == 200
    assert "User Management" in html
    print("  ✓ Admin Users page (/admin/users) loaded (200 OK)")

    status, html, _ = client.get('/admin/components')
    assert status == 200
    assert "Component Management" in html
    print("  ✓ Admin Components page (/admin/components) loaded (200 OK)")

    status, html, _ = client.get('/admin/projects')
    assert status == 200
    assert "Project Management" in html
    print("  ✓ Admin Projects page (/admin/projects) loaded (200 OK)")

    status, html, _ = client.get('/admin/projects/add')
    assert status == 200
    assert "Required Components" in html
    print("  ✓ Admin Add Project page (/admin/projects/add) loaded (200 OK)")

    # 13. Custom 404 Error Page
    print("\n[13] Testing Custom 404 Error Page...")
    status, html, _ = client.get('/this-route-does-not-exist-secondlife')
    assert status == 404, f"Expected 404, got {status}"
    assert "404" in html
    assert "Component Not Found" in html
    print("  ✓ Custom 404 error page successfully returned (404 Not Found)")

    print("\n" + "=" * 70)
    print("✅ ALL LIVE HTTP SERVER TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 70)


if __name__ == '__main__':
    run_live_tests()
