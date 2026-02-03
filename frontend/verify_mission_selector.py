import re

from playwright.sync_api import expect, sync_playwright


def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Mock User API
    page.route("**/api/security/user/me", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"id": "123", "email": "test@test.com", "full_name": "Test User", "is_admin": false}'
    ))

    # Mock Conversations API
    page.route("**/api/chat/conversations", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='[]'
    ))

    # Set token in localStorage before load
    page.add_init_script("""
        localStorage.setItem('token', 'fake-jwt-token');
    """)

    # Navigate
    page.goto("http://localhost:3000")

    # Wait for Dashboard
    expect(page.get_by_text("Overmind Education")).to_be_visible(timeout=10000)

    # Check for Mission Selector
    mission_btn = page.get_by_text("المهمة الخارقة")
    expect(mission_btn).to_be_visible()

    # Click it
    mission_btn.click()

    # Verify active state
    btn_locator = page.locator("button.mission-btn", has_text="المهمة الخارقة")
    # The class attribute should contain 'active'. Using regex to match it.
    expect(btn_locator).to_have_class(re.compile(r"active"))

    # Take Screenshot
    page.screenshot(path="verification_mission_selector.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
