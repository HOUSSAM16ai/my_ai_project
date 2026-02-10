import re

from playwright.sync_api import expect, sync_playwright


def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Mock User API
    page.route(
        "**/api/security/user/me",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"id": "123", "email": "test@test.com", "full_name": "Test User", "is_admin": false}',
        ),
    )

    # Mock Conversations API
    page.route(
        "**/api/chat/conversations",
        lambda route: route.fulfill(status=200, content_type="application/json", body="[]"),
    )

    # Set token in localStorage before load
    page.add_init_script("""
        localStorage.setItem('token', 'fake-jwt-token');
    """)

    # Navigate
    page.goto("http://localhost:3000")

    # Wait for Dashboard
    expect(page.get_by_text("Overmind Education")).to_be_visible(timeout=10000)

    # Verify Status Text (Should be Arabic)
    status_elem = page.locator(".header-status")
    expect(status_elem).to_contain_text(re.compile(r"متصل|جاري الاتصال|غير متصل|خطأ في الاتصال"))

    # Open Mission Modal
    trigger_btn = page.locator("button.mission-trigger-btn")
    expect(trigger_btn).to_be_visible()
    trigger_btn.click()

    # Check for Mission Selector in Modal
    mission_btn = page.locator("button.mission-btn").filter(has_text="المهمة الخارقة")
    expect(mission_btn).to_be_visible()

    # Click it
    mission_btn.click()

    # After clicking, modal closes and mission type changes.
    # We verify the selected mission bar updates
    selected_bar = page.locator(".selected-mission-bar")
    expect(selected_bar).to_contain_text("المهمة الخارقة")

    # Take Screenshot
    page.screenshot(path="verification_mission_selector.png")

    browser.close()


with sync_playwright() as playwright:
    run(playwright)
