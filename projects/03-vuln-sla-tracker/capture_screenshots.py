#!/usr/bin/env python3
"""Capture demo screenshots of the Vuln SLA Tracker using Playwright."""

import os, sys, json, urllib.request, time

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo", "screenshots")
os.makedirs(OUTPUT_DIR, exist_ok=True)

BASE = "http://localhost:3000"
API = "http://localhost:8003"


def check_servers():
    try:
        urllib.request.urlopen(f"{API}/api/v1/health", timeout=3)
    except Exception:
        print("ERROR: Backend not running on port 8003. Run: make api")
        sys.exit(1)
    try:
        urllib.request.urlopen(BASE, timeout=3)
    except Exception:
        print("ERROR: Frontend not running on port 3000. Run: cd ui && npm run dev")
        sys.exit(1)


def api(method, path, data=None, token=None):
    url = f"{API}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, method=method, headers=headers)
    if data:
        req.data = json.dumps(data).encode()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"API error ({path}): {e}")
        return None


check_servers()

# Ensure demo user exists
api("POST", "/api/v1/auth/register", {"email": "demo@vodafone.com", "password": "demo123"})

# Login
login = api("POST", "/api/v1/auth/login", {"email": "demo@vodafone.com", "password": "demo123"})
TOKEN = login["access_token"]
print(f"Logged in as: {login['user']['email']}")

# Seed fresh data
print("Seeding demo data...")
os.system(f"cd {os.path.dirname(os.path.abspath(__file__))} && python3 -m src.seed_data 2>/dev/null")
time.sleep(1)

from playwright.sync_api import sync_playwright

screenshots = [
    ("01-login", "/login", "Sign in page with Vuln SLA Tracker branding"),
    ("02-dashboard", "/", "Dashboard — KPI cards, severity distribution, breach trend, top overdue table"),
    ("03-dashboard-scrolled", "/", "Dashboard scrolled — top overdue vulnerabilities table with SLA breach days"),
    ("04-vulnerabilities", "/vulnerabilities?severity=Critical&sla_breach=breached", "Vulnerability list — filtered to Critical + SLA breached"),
    ("05-vulnerabilities-all", "/vulnerabilities", "Full vulnerability list with search, severity/status/SLA filters"),
    ("06-scanner-runs", "/scanner-runs", "Scanner import history with CSV upload button"),
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
    page = context.new_page()

    # Set auth token
    page.goto(BASE + "/login", wait_until="networkidle")
    page.evaluate(f"""
        localStorage.setItem("itgc_token", "{TOKEN}");
        localStorage.setItem("itgc_user", JSON.stringify({json.dumps(login["user"])}));
    """)

    for name, path, description in screenshots:
        print(f"Capturing: {name} — {description}")
        page.goto(BASE + path, wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(OUTPUT_DIR, f"{name}.png"), full_page=(name == "03-dashboard-scrolled"))
        print(f"  Saved: {name}.png")

    browser.close()

files = sorted(os.listdir(OUTPUT_DIR))
print(f"\nDone! {len(files)} screenshots saved to {OUTPUT_DIR}:")
for f in files:
    size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
    print(f"  {f} ({size:,} bytes)")
