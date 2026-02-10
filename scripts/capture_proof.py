from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("file:///app/scripts/proof.html")
        page.screenshot(path="proof_of_success.png")
        browser.close()

if __name__ == "__main__":
    run()
