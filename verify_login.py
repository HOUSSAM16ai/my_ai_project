import asyncio
from playwright.async_api import async_playwright, expect

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        try:
            print("Navigating to the REAL application...")
            await page.goto("http://localhost:8000/", timeout=60000)

            print("Waiting for the TRUE login form to appear...")
            await expect(page.locator('input[type="email"]')).to_be_visible(timeout=30000)
            await expect(page.locator('input[type="password"]')).to_be_visible(timeout=30000)
            print("SUCCESS: The REAL login form is visible!")

            print("Performing login with correct credentials...")
            await page.fill('input[type="email"]', "admin@cogniforge.com")
            await page.fill('input[type="password"]', "SecureAdminP@ssw0rd")
            await page.locator('button[type="submit"]').click()

            print("Waiting for admin dashboard to load with the CORRECT text...")
            await page.wait_for_selector("text='Neural Interface (Live)'", timeout=30000)
            print("ULTIMATE SUCCESS: Admin dashboard loaded and the correct text is verified!")

            screenshot_path = "admin_dashboard_ULTIMATE_SUCCESS.png"
            await page.screenshot(path=screenshot_path)
            print(f"Final, conclusive proof captured: {screenshot_path}")

        except Exception as e:
            print(f"A failure occurred during the final, corrected verification: {e}")
            await page.screenshot(path="final_corrected_verification_error.png")
            raise

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
