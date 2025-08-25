import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright, Page

from login_utils import is_logged_in, perform_login, LOGIN_DATA_DIR
from schedule_post_logic import schedule_post
from screenshot_helper import SCREENSHOT_DIR, start_new_log, log_action

# --- Configuration ---
SCHEDULE_FILE = Path("./schedule.json")

def main():
    print("\n--- Starting Schedule Posts Runner ---")
    
    # Ensure necessary directories exist
    LOGIN_DATA_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    
    # Read schedule.json
    if not SCHEDULE_FILE.exists():
        print(f"❌ Error: {SCHEDULE_FILE} not found. Run generate_schedule_file.py first.")
        sys.exit(1)
    
    try:
        with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
            scheduled_items = json.load(f)
        print(f"✅ Loaded {len(scheduled_items)} items from {SCHEDULE_FILE}.")
    except json.JSONDecodeError as e:
        print(f"❌ Error decoding JSON from {SCHEDULE_FILE}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading {SCHEDULE_FILE}: {e}")
        sys.exit(1)

    if not scheduled_items:
        print("ℹ️ Schedule file is empty. Nothing to schedule.")
        sys.exit(0)

    # --- Playwright Session Management (Single Browser) ---
    with sync_playwright() as p:
        browser_context = None
        try:
            print("🌐 Launching single persistent browser session...")
            browser_context = p.chromium.launch_persistent_context(
                user_data_dir=str(LOGIN_DATA_DIR),
                headless=True,
                viewport={"width": 1280, "height": 800},
            )
            page = browser_context.new_page()
            page.goto("https://twitter.com/home", timeout=60000)
            log_action(page, "runner_goto_home_on_start")

            # --- Login Check and Execution ---
            if not is_logged_in(page):
                print("⚠️ Session invalid or not logged in. Attempting full login.")
                if not perform_login(page):
                    raise Exception("Login failed, cannot proceed with scheduling.")
            else:
                print("✅ Reused existing session successfully.")

            # --- Process Scheduled Items ---
            print("\n--- Starting to process scheduled items ---")
            for item in scheduled_items:
                title = item.get("title")
                timestamp_str = item.get("timestamp")

                if not all([title, timestamp_str]):
                    print(f"⚠️ Skipping item due to missing title or timestamp: {item}", file=sys.stderr)
                    continue
                
                try:
                    # Ensure the timestamp is timezone-aware for comparison if needed
                    item_datetime = datetime.fromisoformat(timestamp_str)
                    if item_datetime.tzinfo is None: # Assume UTC if no timezone info
                        item_datetime = item_datetime.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    print(f"⚠️ Skipping item due to invalid datetime format: '{timestamp_str}'", file=sys.stderr)
                    continue

                tweet_text = title # No URL in new schema
                schedule_post(page, tweet_text, item_datetime)
                
                delay = random.uniform(2.0, 3.0)
                print(f"\n--- Waiting {delay:.3f}s before next scheduling action ---")
                time.sleep(delay)

            print("\n--- All scheduled items processed. ---")

        except Exception as e:
            print(f"❌ A critical error occurred in schedule_posts_runner: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            if browser_context:
                browser_context.close()
                print("🌐 Browser session closed.")
    
    print("\n--- Schedule Posts Runner finished. ---")
    sys.exit(0)

if __name__ == "__main__":
    main()