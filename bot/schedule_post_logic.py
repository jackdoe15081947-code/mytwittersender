import sys
import time
import random
from datetime import datetime
from playwright.sync_api import Page, TimeoutError
from screenshot_helper import start_new_log, log_action

def schedule_post(page: Page, tweet_text: str, item_time: datetime):
    """
    Schedules a tweet, with a cleanup step and a final navigation to home.
    """
    start_new_log()
    print(f"   Attempting to schedule for {item_time.strftime('%Y-%m-%d %I:%M %p')}...")
    try:
        page.click('[data-testid="SideNav_NewTweet_Button"]')
        log_action(page, "click-new-tweet-button")
        
        delay_1 = random.uniform(1.0, 2.0)
        print(f"   ...waiting {delay_1:.3f}s")
        time.sleep(delay_1)

        page.fill('div[data-testid="tweetTextarea_0"]', tweet_text, timeout=10000)
        log_action(page, "fill-tweet-text")

        delay_2 = random.uniform(0.5, 1.0)
        print(f"   ...waiting {delay_2:.3f}s")
        time.sleep(delay_2)
        
        page.click("button[data-testid='scheduleOption']")
        log_action(page, "click-schedule-icon")
        
        delay_3 = random.uniform(1.0, 1.5)
        print(f"   ...waiting {delay_3:.3f}s")
        time.sleep(delay_3)

        schedule_date = item_time.strftime("%Y-%m-%d")
        hour = item_time.strftime("%-I")
        minute = str(item_time.minute)
        ampm = item_time.strftime("%p")
        
        print(f"   ...setting schedule: {schedule_date} {hour}:{minute.zfill(2)} {ampm} using ID selectors")
        page.fill('input[type="date"]', schedule_date)
        log_action(page, "fill-date")
        
        page.select_option("select#SELECTOR_4", hour)
        log_action(page, "select-hour-with-id")

        page.select_option("select#SELECTOR_5", minute)
        log_action(page, "select-minute-with-id")
        
        page.select_option("select#SELECTOR_6", ampm)
        log_action(page, "select-ampm-with-id")
        
        delay_4 = random.uniform(0.5, 1.0)
        print(f"   ...waiting {delay_4:.3f}s")
        time.sleep(delay_4)

        page.click("button[data-testid='scheduledConfirmationPrimaryAction']")
        log_action(page, "click-confirm-schedule")
        
        delay_5 = random.uniform(1.5, 2.0)
        print(f"   ...waiting {delay_5:.3f}s for final confirmation")
        time.sleep(delay_5)

        final_btn = page.locator('button[data-testid="tweetButton"]')
        final_btn.wait_for(state="visible", timeout=15000)
        final_btn.click()
        log_action(page, "click-final-schedule-button")

        page.wait_for_timeout(4000)
        log_action(page, "SUCCESS")
        print("  ✅ Tweet scheduled successfully.")

        # --- Pop-up Cleanup Logic ---
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
        
        # --- ADDED: Go to home page to reset state ---
        print("   ...navigating to home page to ensure a clean state for the next run.")
        page.goto("https://twitter.com/home")
        log_action(page, "navigated-home-after-success")
        # --- End of added step ---

    except (TimeoutError, Exception) as e:
        print(f"  ❌ FAILED to schedule tweet. Error: {e}", file=sys.stderr)
        log_action(page, "FAILURE")
        page.goto("https://twitter.com/home")
