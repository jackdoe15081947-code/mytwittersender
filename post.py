from playwright.sync_api import Page
from pathlib import Path
from datetime import datetime
import time
import json

debug_dir = Path("data/schedule_logs")
debug_dir.mkdir(parents=True, exist_ok=True)

def log_page(page: Page, name: str):
    time.sleep(2)
    page.screenshot(path=debug_dir / f"{name}.png")
    (debug_dir / f"{name}.txt").write_text(page.inner_text("body"), encoding="utf-8")
    (debug_dir / f"{name}.html").write_text(page.content(), encoding="utf-8")
    print(f"✅ Logged: {name}")

def schedule_posts_from_json(page: Page):
    try:
        with open("schedule.json", "r") as f:
            schedule_data = json.load(f)
    except FileNotFoundError:
        print("❌ schedule.json not found.")
        return
    except json.JSONDecodeError:
        print("❌ Could not decode schedule.json.")
        return

    for i, item in enumerate(schedule_data):
        tweet_text = item.get("title")
        timestamp_str = item.get("timestamp")

        if not tweet_text or not timestamp_str:
            print(f"⚠️ Skipping item {i+1} due to missing data.")
            continue

        print(f"\n--- Scheduling Post {i+1}: '{tweet_text}' for {timestamp_str} ---")
        
        # Parse timestamp and format for twitter scheduler
        dt_obj = datetime.fromisoformat(timestamp_str)
        schedule_date = dt_obj.strftime("%Y-%m-%d")
        hour = dt_obj.strftime("%I").lstrip("0")
        minute = dt_obj.strftime("%M")
        ampm = dt_obj.strftime("%p")

        page.goto("https://twitter.com/home", wait_until="load")
        page.wait_for_timeout(5000)
        log_page(page, f"{i+1}_1_home_loaded")

        page.click('[data-testid="SideNav_NewTweet_Button"]')
        page.wait_for_timeout(2000)
        log_page(page, f"{i+1}_2_composer_opened")

        print(f"🔹 Typing tweet: {tweet_text}")
        page.fill('div[data-testid="tweetTextarea_0"]', tweet_text)
        log_page(page, f"{i+1}_3_text_filled")

        print("🔹 Opening schedule modal...")
        page.click("button[data-testid='scheduleOption']")
        page.wait_for_timeout(2000)
        log_page(page, f"{i+1}_4_schedule_modal_opened")

        print(f"🔹 Setting schedule: {schedule_date} {hour}:{minute} {ampm}")
        page.fill('input[type="date"]', schedule_date)
        page.select_option("select#SELECTOR_4", hour)
        page.select_option("select#SELECTOR_5", minute)
        page.select_option("select#SELECTOR_6", ampm)
        log_page(page, f"{i+1}_5_date_time_set")

        print("🔹 Confirming schedule modal...")
        page.click("button[data-testid='scheduledConfirmationPrimaryAction']")
        page.wait_for_timeout(3000)
        log_page(page, f"{i+1}_6_schedule_modal_confirmed")

        print("🔹 Finalizing tweet scheduling...")
        try:
            final_btn = page.locator('button[data-testid="tweetButton"]')
            final_btn.wait_for(state="visible", timeout=15000)
            final_btn.click(force=True, timeout=10000)
            page.wait_for_timeout(4000)
            log_page(page, f"{i+1}_7_tweet_scheduled_final")
            print(f"✅ Tweet '{tweet_text}' successfully scheduled!")
        except Exception as e:
            print(f"❌ Failed to click final schedule button for '{tweet_text}': {e}")
            log_page(page, f"{i+1}_7_schedule_failed")
