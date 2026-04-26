#!/usr/bin/env python3
"""Capture demo screenshots of the Evidence Collection Automator using Playwright."""

import os
import sys
import json
import urllib.request
import time

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo", "screenshots")
os.makedirs(OUTPUT_DIR, exist_ok=True)

BASE = "http://localhost:3001"
API = "http://localhost:8002"


def check_servers():
    try:
        urllib.request.urlopen(f"{API}/api/v1/health", timeout=3)
    except Exception:
        print("ERROR: Backend not running on port 8002.")
        sys.exit(1)
    try:
        urllib.request.urlopen(BASE, timeout=3)
    except Exception:
        print("ERROR: Frontend not running on port 3001.")
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
        print(f"API error: {e}")
        return None


check_servers()

# Ensure demo user exists
api("POST", "/api/v1/auth/register", {"email": "demo@vodafone.com", "password": "Demo123!"})

# Login
login = api("POST", "/api/v1/auth/login", {"email": "demo@vodafone.com", "password": "Demo123!"})
TOKEN = login["access_token"]
print(f"Logged in as: {login['user']['email']}")

# Set AD connector to simulated mode (ensure clean demo state)
connectors = api("GET", "/api/v1/connectors") or []
for c in connectors:
    api("PATCH", f"/api/v1/connectors/{c['id']}", {"mode": "simulated"}, token=TOKEN)

# Run a connector to ensure there's fresh data
api("POST", "/api/v1/connectors/1/run", {"market_id": 12}, token=TOKEN)  # AD → Ireland

# Get collection ID for the detail screenshot
collections = api("GET", "/api/v1/collections", token=TOKEN) or []
collection_id = collections[0]["id"] if collections else 1

# Get an evidence item ID for the evidence detail
evidence = api("GET", "/api/v1/evidence?limit=5") or []
evidence_item_id = evidence[0]["id"] if evidence else 1

from playwright.sync_api import sync_playwright

screenshots = [
    ("01-login", "/login", "Sign in page with Vodafone-branded dark theme"),
    ("02-dashboard", "/", "Dashboard — evidence stats, connector status grid, quick links"),
    ("03-connectors", "/connectors", "7 connectors with SIM/LIVE mode badges, market selector, Run buttons"),
    ("04-collections", "/collections", "Collection history with status, timestamps, control tags"),
    ("05-collection-detail", f"/collections/{collection_id}", "Expanded collection with rendered evidence tables"),
    ("06-evidence-library", "/evidence", "Evidence library — search, filter, expandable cards with formatted data"),
    ("07-bundles", "/bundles", "Bundle builder — multi-select evidence, name, export, assess"),
    ("08-evidence-rendered", "/evidence", "Evidence card expanded — tables, stat grids, severity badges"),
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        device_scale_factor=2,
    )
    page = context.new_page()

    # Set auth token in localStorage
    page.goto(BASE + "/login", wait_until="networkidle")
    page.evaluate(f"""
        localStorage.setItem("itgc_token", "{TOKEN}");
        localStorage.setItem("itgc_user", JSON.stringify({json.dumps(login["user"])}));
    """)

    for name, path, description in screenshots:
        print(f"Capturing: {name} — {description}")
        page.goto(BASE + path, wait_until="networkidle")
        page.wait_for_timeout(2000)  # Let animations finish

        # For evidence-rendered, expand the first evidence card
        if name == "08-evidence-rendered":
            try:
                expand_btn = page.locator("button.w-full.p-4").first
                if expand_btn.is_visible():
                    expand_btn.click()
                    page.wait_for_timeout(1500)
            except Exception as e:
                print(f"  Expand evidence: {e}")

        page.screenshot(
            path=os.path.join(OUTPUT_DIR, f"{name}.png"),
            full_page=False,
        )
        print(f"  Saved: {name}.png")

    browser.close()

# Verify
files = os.listdir(OUTPUT_DIR)
print(f"\nDone! {len(files)} screenshots saved to {OUTPUT_DIR}:")
for f in sorted(files):
    size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
    print(f"  {f} ({size:,} bytes)")
