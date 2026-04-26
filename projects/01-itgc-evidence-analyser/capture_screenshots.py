#!/usr/bin/env python3
"""Capture demo screenshots of the ITGC Evidence Analyser using Playwright."""

import subprocess
import sys
import os
import time

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo", "screenshots")
os.makedirs(OUTPUT_DIR, exist_ok=True)

BASE = "http://localhost:3000"
API = "http://localhost:8001"

def check_servers():
    import urllib.request
    try:
        urllib.request.urlopen(f"{API}/api/v1/health", timeout=3)
    except Exception:
        print("ERROR: Backend not running on port 8001. Start with: uvicorn src.api:app --port 8001")
        sys.exit(1)
    try:
        urllib.request.urlopen(BASE, timeout=3)
    except Exception:
        print("ERROR: Frontend not running on port 3000. Start with: cd ui && npm run dev")
        sys.exit(1)

check_servers()

# Seed admin + create a demo assessment via API
import urllib.request
import json

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

# Ensure admin exists
api("POST", "/api/v1/auth/register", {"email": "demo@vodafone.com", "password": "Demo123!"})

# Login
login = api("POST", "/api/v1/auth/login", {"email": "demo@vodafone.com", "password": "Demo123!"})
TOKEN = login["access_token"]
print(f"Logged in as: {login['user']['email']}")

# Create a demo assessment for screenshots
result = api("POST", "/api/v1/assess", {
    "control_id": "ENDPOINT_001",
    "evidence_text": "DEMO: Mobile Device Policy v3.2 approved by CISO on 2026-03-15. All smartphones (iOS 17+, Android 14+) and tablets (iPadOS 17+, Android 14+) registered in Microsoft Intune MDM. Multi-factor authentication enforced via Entra ID Conditional Access. Full-disk encryption enabled on all enrolled devices. Policy communicated via Workplace intranet and annual security awareness training. Quarterly policy review conducted — last review 2026-01-10. Acceptable Use Policy signed by 100% of users at onboarding.",
    "statement_type": "D",
    "market_id": 12,
    "samples": ["Smart phones", "Tablets"],
}, token=TOKEN)

print(f"Demo assessment: {result.get('verdict', 'FAILED')}")

# Now capture screenshots
from playwright.sync_api import sync_playwright

screenshots = [
    ("01-login", "/login", "Sign in page with email/password form"),
    ("02-dashboard", "/", "Dashboard with assessment counts and domain breakdown"),
    ("03-controls", "/controls", "Controls library — 58 ITGC controls searchable"),
    ("04-control-detail", "/controls/ENDPOINT_001", "Control detail with D and E statements"),
    ("05-assess", "/assess", "Assessment runner — market, control, samples, evidence upload"),
    ("06-assessments", "/assessments", "Assessment history with expandable audit cards"),
    ("07-markets", "/markets", "Markets directory — 32 Vodafone subsidiaries"),
    ("08-chat", "/", "Dashboard with chat widget open"),  # Will open chat on dashboard
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
        page.wait_for_timeout(1500)  # Let animations finish

        # For chat screenshot, click the chat button
        if name == "08-chat":
            try:
                chat_btn = page.locator(".chat-trigger").first
                if chat_btn.is_visible():
                    chat_btn.click()
                    page.wait_for_timeout(1500)
                    # Type a message
                    chat_input = page.locator(".chat-input-row input").first
                    if chat_input.is_visible():
                        chat_input.fill("Review the ENDPOINT_001 assessment for me")
                        page.locator(".chat-input-row button").first.click()
                        page.wait_for_timeout(3000)
            except Exception as e:
                print(f"  Chat interaction: {e}")

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
