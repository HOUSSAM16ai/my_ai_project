import os
import time
from playwright.sync_api import sync_playwright

def verify_login_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Create a context with console log capture
        context = browser.new_context()
        page = context.new_page()

        # Capture console messages to check for SyntaxError
        page.on("console", lambda msg: print(f"Console: {msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: print(f"Page Error: {err}"))

        try:
            print("Navigating to http://127.0.0.1:34567/...")
            page.goto("http://127.0.0.1:34567/")

            # Wait for content to load. If it's blank/crashed, this might timeout or show nothing.
            # We look for the "Admin Login" text or the root element
            print("Waiting for login form...")
            page.wait_for_selector(".login-form", timeout=5000)

            # Check if performance monitor loaded correctly (no SyntaxError in console implies success, but we can check existence)
            # We can evaluate js to check if PerformanceMonitor is defined
            is_defined = page.evaluate("typeof window.PerformanceMonitor !== 'undefined'")
            print(f"PerformanceMonitor defined: {is_defined}")

            if not is_defined:
                print("FAILURE: PerformanceMonitor is NOT defined.")
            else:
                print("SUCCESS: PerformanceMonitor is defined.")

            # Take screenshot
            screenshot_path = "/home/jules/verification/login_page_fixed.png"
            page.screenshot(path=screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")

        except Exception as e:
            print(f"Verification failed: {e}")
            page.screenshot(path="/home/jules/verification/failure.png")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_login_page()
