from playwright.sync_api import sync_playwright

def test_chat_stream_throttling():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to the local server
        page.goto("http://localhost:8000/index.html")

        # Mock API responses
        # 1. Mock User/Auth endpoints
        page.route('**/api/security/user/me', lambda route: route.fulfill(
            status=200,
            body='{"name": "Test Admin", "email": "admin@test.com", "is_admin": true, "id": 1}',
            headers={'Content-Type': 'application/json'}
        ))

        # 2. Mock Conversations list
        page.route('**/admin/api/conversations', lambda route: route.fulfill(
            status=200,
            body='[{"conversation_id": 1, "title": "Test Chat", "created_at": "2023-01-01"}]',
            headers={'Content-Type': 'application/json'}
        ))

        # 3. Mock Latest Chat
        page.route('**/admin/api/chat/latest', lambda route: route.fulfill(
            status=200,
            body='{"conversation_id": 1, "title": "Test Chat", "messages": []}',
            headers={'Content-Type': 'application/json'}
        ))

        # 4. Mock Stream Endpoint
        def handle_stream(route):
            stream_body = ""
            chunks = ["Hello", " ", "World", " ", "This", " ", "is", " ", "a", " ", "test."]
            for chunk in chunks:
                data = '{"choices": [{"delta": {"content": "' + chunk + '"}}]}'
                stream_body += f"data: {data}\n\n"
            stream_body += "data: [DONE]\n\n"

            route.fulfill(
                status=200,
                body=stream_body,
                headers={'Content-Type': 'text/event-stream'}
            )

        page.route('**/admin/api/chat/stream', handle_stream)

        # Set token (now it should work as we are on localhost)
        page.evaluate("localStorage.setItem('token', 'fake-token')")
        page.reload()

        # Wait for Dashboard to load
        page.wait_for_selector('h2:has-text("Overmind CLI Mindgate")')

        # Type a message
        page.fill('textarea', 'Hello Overmind')

        # Click Send
        page.click('.input-area button')

        # Wait for the response to appear
        page.wait_for_selector('.message.assistant')

        # Take screenshot
        page.screenshot(path='verification/frontend_verification.png')
        print("Screenshot saved to verification/frontend_verification.png")

if __name__ == "__main__":
    test_chat_stream_throttling()
