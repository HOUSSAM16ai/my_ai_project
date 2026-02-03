from playwright.sync_api import sync_playwright, expect
import re

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Mock Admin User API
    page.route("**/api/security/user/me", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"id": "999", "email": "admin@overmind.com", "full_name": "Supreme Admin", "is_admin": true}'
    ))

    # Mock Admin Conversations API
    page.route("**/admin/api/conversations", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='[]'
    ))

    # Set token in localStorage before load
    page.add_init_script("""
        localStorage.setItem('token', 'fake-admin-jwt-token');
    """)

    # Navigate
    page.goto("http://localhost:3000")

    # Wait for Dashboard - Admin Header
    expect(page.get_by_text("OVERMIND CLI")).to_be_visible(timeout=10000)

    # Check for Mission Selector (Should be present for Admin too)
    mission_btn = page.get_by_text("المهمة الخارقة")
    expect(mission_btn).to_be_visible()

    # Click it
    mission_btn.click()

    # Verify active state
    btn_locator = page.locator("button.mission-btn", has_text="المهمة الخارقة")
    expect(btn_locator).to_have_class(re.compile(r"active"))

    # Take Screenshot
    page.screenshot(path="verification_admin_mission_selector.png")
    print("Screenshot saved to verification_admin_mission_selector.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
