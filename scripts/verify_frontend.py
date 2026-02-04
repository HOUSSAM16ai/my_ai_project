import sys
import time

import requests
from bs4 import BeautifulSoup

BASE_URL = "http://127.0.0.1:8000"
MAX_RETRIES = 5
RETRY_DELAY = 5  # seconds


def check_health():
    """Checks the health endpoint."""
    url = f"{BASE_URL}/system/health"
    print(f"Checking health endpoint: {url}...")
    response = requests.get(url)
    response.raise_for_status()
    print("✅ Health endpoint is OK.")


def check_root_div():
    """Checks for the root div in the main page."""
    url = BASE_URL
    print(f"Checking for root div at: {url}...")
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    if not soup.find("div", id="root"):
        raise Exception("❌ Root div not found in the main page.")
    print("✅ Root div is present.")


def main():
    """Main verification function with retries."""
    for i in range(MAX_RETRIES):
        try:
            print(f"--- Verification attempt {i + 1}/{MAX_RETRIES} ---")
            check_health()
            check_root_div()
            print("\n🎉 All checks passed successfully! 🎉")
            sys.exit(0)
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

        if i < MAX_RETRIES - 1:
            print(f"Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)

    print("\n💥 Verification failed after multiple retries. 💥")
    sys.exit(1)


if __name__ == "__main__":
    main()
