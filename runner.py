from playwright.sync_api import sync_playwright
from pathlib import Path
import login
import post

USER_DATA_DIR = Path("login")

def main():
    browser = None
    with sync_playwright() as p:
        try:
            browser, page = login.get_logged_in_page(p, USER_DATA_DIR)
            post.schedule_posts_from_json(page)
            print("✅ All posts scheduled successfully.")
        except Exception as e:
            print(f"❌ An error occurred in the main runner: {e}")
        finally:
            if browser:
                print("🔹 Closing browser session.")
                browser.close()

if __name__ == "__main__":
    main()