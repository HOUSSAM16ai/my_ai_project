
import asyncio
from playwright.async_api import async_playwright, expect

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        try:
            print("Navigating to http://localhost:8000...")
            await page.goto("http://localhost:8000", timeout=15000)

            print("Waiting for login form...")
            await expect(page.locator('input[placeholder="Email"]')).to_be_visible(timeout=10000)
            await expect(page.locator('input[placeholder="Password"]')).to_be_visible()

            print("Entering admin credentials...")
            await page.fill('input[placeholder="Email"]', "admin@cogniforge.com")
            await page.fill('input[placeholder="Password"]', "secureadminpassword")

            print("Clicking login button...")
            await page.click('button[type="submit"]')

            print("Waiting for admin dashboard...")
            await expect(page.locator("h2:has-text('Overmind CLI Mindgate')")).to_be_visible(timeout=10000)
            print("SUCCESS: Admin dashboard is visible!")

            await page.screenshot(path="final_verification.png")
            print("Screenshot 'final_verification.png' captured.")

        except Exception as e:
            print(f"AN ERROR OCCURRED: {e}")
            await page.screenshot(path="error_screenshot.png")
            raise
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
