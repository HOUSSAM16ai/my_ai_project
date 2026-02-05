
from playwright.sync_api import sync_playwright
import os

def capture_verification():
    file_path = os.path.abspath("verification/repro_ui.html")
    url = f"file://{file_path}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        # Take a screenshot of the whole page (both phones)
        screenshot_path = "verification/fix_verification.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot saved to {screenshot_path}")
        browser.close()

if __name__ == "__main__":
    capture_verification()
