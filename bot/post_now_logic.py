import sys
import time
import random
from playwright.sync_api import Page, TimeoutError
from screenshot_helper import start_new_log, log_action

def post_now(page: Page, tweet_text: str):
    """
    Posts a tweet immediately, with the original dynamic delay logic restored.
    """
    start_new_log()
    print(f"   Attempting to post now with restored delay logic: '{tweet_text[:30]}...'")
    try:
        tweet_area_selector = 'div[data-testid="tweetTextarea_0"]'
        post_button_selector = 'button[data-testid="tweetButtonInline"]'

        # --- Posting Logic from working script ---
        # 1. Wait for the main tweet input area to be visible.
        page.wait_for_selector(tweet_area_selector, timeout=15000)
        log_action(page, "waited-for-textarea")
        print("   ✅ Text area is visible.")

        # 2. Type the tweet directly.
        page.fill(tweet_area_selector, tweet_text)
        log_action(page, "fill-text")
        print(f"   🔹 Typing tweet: \"{tweet_text[:30]}...\"")

        # 3. --- DYNAMIC DELAY RESTORED ---
        pre_post_delay = random.uniform(2.5, 3.5)
        print(f"   ...waiting {pre_post_delay:.3f}s (pre-post)")
        time.sleep(pre_post_delay)
        # --- END OF RESTORED LOGIC ---

        # 4. Click the "Post" button.
        print("   🔹 Clicking the Post button...")
        page.locator(post_button_selector).click(timeout=10000)
        log_action(page, "click-post")

        # 5. --- ORIGINAL WAIT RESTORED ---
        # Using the original 4-second wait for confirmation.
        page.wait_for_timeout(4000)
        log_action(page, "SUCCESS")
        print("  ✅ Tweet posted successfully.")
        # --- END OF RESTORED LOGIC ---


        # --- Existing Cleanup Logic (Unchanged) ---
        print("   ...entering cleanup step.")
        time.sleep(2)

        page_text = page.inner_text("body").lower()

        if "you've unlocked more" in page_text or "got it" in page_text or "learn more" in page_text:
            print("   -> Known pop-up detected. Clicking at (640, 650) to close.")
            page.mouse.click(640, 650)
            log_action(page, "clicked-close-popup")
            print("   ✅ Pop-up closed.")
        else:
            print("   -> No known pop-up text found. Assuming page is clean.")

        print("   ...navigating to home page to ensure a clean state for the next run.")
        page.goto("https://twitter.com/home")
        log_action(page, "navigated-home-after-success")
        # --- End of Cleanup Logic ---

    except (TimeoutError, Exception) as e:
        print(f"  ❌ FAILED to post tweet. Error: {e}", file=sys.stderr)
        log_action(page, "FAILURE")
        page.goto("https://twitter.com/home")
