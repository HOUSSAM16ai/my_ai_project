import asyncio

from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        try:
            await page.goto("http://localhost:5000/admin/dashboard")

            # This assumes you have a way to log in; for now, we'll just check the badge
            # In a real test, you'd fill in login credentials

            # Wait for the WebSocket connected badge to appear
            await page.wait_for_selector("text=⚡ WebSocket Connected", timeout=30000)
            print("✅ WebSocket Connected badge found.")

            # Send a message and check for a response
            await page.fill("#chat-input", "Hello WebSocket")
            await page.click("#send-btn")

            # Wait for the response to start streaming in
            await page.wait_for_selector(
                ".message.assistant .message-content:has-text('This is a streamed response')",
                timeout=10000,
            )
            print("✅ Received streamed response.")

            await page.screenshot(path="screenshot.png")
            print("📸 Screenshot taken.")

        except Exception as e:
            print(f"❌ Verification failed: {e}")
            await page.screenshot(path="error.png")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
