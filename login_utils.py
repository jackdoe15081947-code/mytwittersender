import os
import sys
import time
from pathlib import Path
from playwright.sync_api import Page
from dotenv import load_dotenv

from screenshot_helper import start_new_log, log_action

load_dotenv() # Load environment variables here

# --- Configuration ---
EMAIL = os.getenv("TWITTER_EMAIL")
PASSWORD = os.getenv("TWITTER_PASSWORD")
USERNAME = os.getenv("TWITTER_USERNAME")

# Paths for Playwright persistent context
LOGIN_DATA_DIR = Path("./login/default/login_data")

def is_logged_in(page: Page) -> bool:
    """Checks if the page appears to be logged in."""
    time.sleep(5)
    page_text = page.inner_text("body").lower()
    logged_in = "for you" in page_text or "following" in page_text
    if logged_in:
        print("   Session appears to be logged in.")
    else:
        print("   Session does NOT appear to be logged in.")
    return logged_in

def perform_login(page: Page) -> bool:
    """Performs a full login process on the given Playwright page."""
    if not all([EMAIL, PASSWORD, USERNAME]):
        print("❌ FATAL: TWITTER_EMAIL, TWITTER_PASSWORD, or TWITTER_USERNAME not set in environment for login.", file=sys.stderr)
        return False

    print("🚀 Starting full login process...")
    start_new_log() # Start new screenshot log for the login process
    log_action(page, "start_full_login")
    page.goto("https://x.com/login", timeout=60000)
    time.sleep(5)
    log_action(page, "goto_login_page")
    page.mouse.click(640, 390) # Click on email/username input area
    log_action(page, "click_email_input")
    page.keyboard.type(EMAIL)
    page.mouse.click(640, 475) # Click on next button or password input area
    log_action(page, "type_email")
    time.sleep(5)
    if "unusual login" in page.inner_text("body").lower():
        print("   Detected unusual login prompt, entering username...")
        page.mouse.click(520, 350) # Click on username input area
        log_action(page, "click_username_input_unusual")
        page.keyboard.type(USERNAME)
        page.mouse.click(650, 670) # Click on next/confirm button
        log_action(page, "type_username_unusual")
        time.sleep(5)
    page.mouse.click(600, 340) # Click on password input area
    log_action(page, "click_password_input")
    page.keyboard.type(PASSWORD)
    page.mouse.click(650, 630) # Click on login button
    log_action(page, "type_password")
    time.sleep(7)
    if not is_logged_in(page):
        print("❌ Login failed.", file=sys.stderr)
        log_action(page, "login_failed")
        return False
    print("✅ Full login successful.")
    log_action(page, "login_successful")
    return True