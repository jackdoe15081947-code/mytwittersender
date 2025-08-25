import os
import sys
import json
import time
import random
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright, Page
from dotenv import load_dotenv

from post_now_logic import post_now
from schedule_post_logic import schedule_post

load_dotenv()

# --- Configuration ---
EMAIL = os.getenv("TWITTER_EMAIL")
PASSWORD = os.getenv("TWITTER_PASSWORD")
USERNAME = os.getenv("TWITTER_USERNAME")
BOT_CATEGORY = os.getenv("BOT_CATEGORY")
LOGIN_DATA_DIR = Path(f"./login/{BOT_CATEGORY}/login_data")

# --- Helper Functions (unchanged) ---
def is_logged_in(page: Page):
    time.sleep(5)
    page_text = page.inner_text("body").lower()
    return "for you" in page_text or "following" in page_text

def perform_login(page: Page):
    print("🚀 Starting full login process...")
    page.goto("https://x.com/login", timeout=60000)
    time.sleep(5)
    page.mouse.click(580, 350)
    page.keyboard.type(EMAIL)
    page.mouse.click(640, 430)
    time.sleep(5)
    if "unusual login" in page.inner_text("body").lower():
        page.mouse.click(520, 320)
        page.keyboard.type(USERNAME)
        page.mouse.click(640, 640)
        time.sleep(5)
    page.mouse.click(500, 300)
    page.keyboard.type(PASSWORD)
    page.mouse.click(640, 590)
    time.sleep(7)
    if not is_logged_in(page):
        print("❌ Login failed.", file=sys.stderr)
        return False
    print("✅ Full login successful.")
    return True

# --- Main Orchestration ---
def main():
    if not all([EMAIL, PASSWORD, USERNAME, BOT_CATEGORY]):
        sys.exit("❌ FATAL: Credentials or BOT_CATEGORY not set.")
    if len(sys.argv) < 2:
        sys.exit("❌ FATAL: No data passed.")
    try:
        data = json.loads(sys.argv[1])
        items_to_post_now = data.get("post_now", [])
        items_to_schedule = data.get("schedule", [])
    except json.JSONDecodeError:
        sys.exit("❌ FATAL: Invalid JSON data received from main_controller.")

    with sync_playwright() as p:
        browser = None
        try:
            print(f"--- Starting session for bot: '{BOT_CATEGORY}' ---")
            LOGIN_DATA_DIR.mkdir(parents=True, exist_ok=True)
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(LOGIN_DATA_DIR),
                headless=True,
                viewport={"width": 1280, "height": 800},
            )
            page = browser.new_page()
            page.goto("https://twitter.com/home", timeout=60000)

            if "login" in page.url or not is_logged_in(page):
                print("⚠️ Session invalid. Performing full login.")
                if not perform_login(page):
                     raise Exception("Login failed, cannot proceed.")
            else:
                print("✅ Reused existing session successfully.")

            total_items = len(items_to_post_now) + len(items_to_schedule)
            processed_count = 0

            # Process the "Post Now" Queue
            if items_to_post_now:
                print(f"\n🚀 Processing {len(items_to_post_now)} items from the 'post_now' queue...")
                for item in items_to_post_now:
                    tweet_text = f'{item.get("title", "")}\n\n{item.get("url", "")}'
                    post_now(page, tweet_text)
                    
                    processed_count += 1
                    if processed_count < total_items:
                        delay = random.uniform(2.0, 3.0)
                        print(f"\n--- Waiting {delay:.3f}s before next action ---")
                        time.sleep(delay)
            else:
                print("\nℹ️ 'post_now' queue is empty.")

            # Process the "Schedule" Queue
            if items_to_schedule:
                print(f"\n🚀 Processing {len(items_to_schedule)} items from the 'schedule' queue...")
                for item in items_to_schedule:
                    # --- THIS IS THE FIX ---
                    # Changed "post_at" to "time" to match the key from main_controller
                    time_str = item.get("time")
                    if not time_str:
                        # Updated the error message for clarity
                        print(f"⚠️ Skipping item due to missing 'time' field: {item}", file=sys.stderr)
                        continue
                    
                    try:
                        item_datetime = datetime.fromisoformat(time_str)
                    except (ValueError, TypeError):
                        print(f"⚠️ Skipping item due to invalid datetime format: '{time_str}'", file=sys.stderr)
                        continue

                    tweet_text = f'{item.get("title", "")}\n\n{item.get("url", "")}'
                    schedule_post(page, tweet_text, item_datetime)

                    processed_count += 1
                    if processed_count < total_items:
                        delay = random.uniform(2.0, 3.0)
                        print(f"\n--- Waiting {delay:.3f}s before next action ---")
                        time.sleep(delay)
            else:
                print("\nℹ️ 'schedule' queue is empty.")

            print(f"\n--- Session for bot '{BOT_CATEGORY}' finished successfully. ---")

        except Exception as e:
            print(f"❌ A critical error occurred in process_bot: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            if browser:
                browser.close()

if __name__ == "__main__":
    main()
