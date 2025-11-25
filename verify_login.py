import asyncio
from playwright.async_api import async_playwright, expect

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        try:
            # 1. Verify the Superhuman UI demo page
            print("Navigating to Superhuman UI demo page...")
            await page.goto("http://localhost:8000/superhuman-ui", timeout=60000)
            await expect(page.locator("h1")).to_contain_text("CogniForge Superhuman UI")
            print("✅ Superhuman UI page loaded successfully.")

            # 2. Verify the Admin login page
            print("Navigating to Admin login page...")
            await page.goto("http://localhost:8000/admin/login", timeout=60000)

            # Check for the presence of the login form
            await expect(page.locator('form[action="/admin/login"]')).to_be_visible()
            await expect(page.locator('input[name="username"]')).to_be_visible()
            await expect(page.locator('input[name="password"]')).to_be_visible()
            await expect(page.locator('button[type="submit"]')).to_contain_text("Login")

            print("✅ Admin login page loaded successfully with the correct form.")

            # 3. Take a screenshot
            screenshot_path = "admin_login_page.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 Screenshot saved to {screenshot_path}")

        except Exception as e:
            print(f"❌ An error occurred: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
