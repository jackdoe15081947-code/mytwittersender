from playwright.sync_api import Playwright, sync_playwright, Page, BrowserContext
from pathlib import Path
import os

EMAIL = os.getenv("TWITTER_EMAIL")
USERNAME = os.getenv("TWITTER_USERNAME")
PASSWORD = os.getenv("TWITTER_PASSWORD")

# Ensure folders exist
screenshot_dir = Path("screenshots")
screenshot_dir.mkdir(exist_ok=True)
text_dir = Path("pagetext")
text_dir.mkdir(exist_ok=True)


CHECK_TEXT = """Enter your phone number or username
There was unusual login activity on your account. To help keep your account safe, please enter your phone number or username to verify it’s you.
Phone or username
Next"""

def take_shot(page: Page, name: str):
    page.screenshot(path=screenshot_dir / f"{name}.png")
    print(f"✅ Screenshot saved: {name}.png")

def save_text(page: Page, name: str):
    text_path = text_dir / f"{name}.txt"
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(page.inner_text("body"))
    print(f"✅ Page text saved: {name}.txt")

def _is_logged_in(page: Page):
    page.wait_for_timeout(3000)
    page_text = page.inner_text("body")
    return "Home" in page_text or "Tweet" in page_text

def _perform_full_login(p: Playwright, user_data_dir: Path):
    browser = p.chromium.launch_persistent_context(
        user_data_dir=str(user_data_dir),
        headless=True,
        viewport={"width": 1280, "height": 720}
    )
    page = browser.new_page()

    page.goto("https://twitter.com/login")
    page.wait_for_timeout(5000)
    take_shot(page, "1_initial_login")
    save_text(page, "1_initial_login")

    page.mouse.click(580, 350)
    page.keyboard.type(EMAIL)
    page.wait_for_timeout(2000)
    take_shot(page, "2_email_entered")
    save_text(page, "2_email_entered")

    page.mouse.click(640, 430)
    page.wait_for_timeout(5000)
    take_shot(page, "3_after_first_next")
    save_text(page, "3_after_first_next")

    page_text = page.inner_text("body")
    if CHECK_TEXT in page_text:
        print("🔹 Extra verification detected. Entering username.")
        page.mouse.click(520, 320)
        page.keyboard.type(USERNAME)
        page.wait_for_timeout(2000)
        take_shot(page, "4_extra_username_entered")
        save_text(page, "4_extra_username_entered")

        page.mouse.click(640, 640)
        page.wait_for_timeout(5000)
        take_shot(page, "5_after_extra_next")
        save_text(page, "5_after_extra_next")
    else:
        print("✅ No extra verification. Continuing.")

    page.mouse.click(500, 300)
    page.keyboard.type(PASSWORD)
    page.wait_for_timeout(2000)
    take_shot(page, "6_password_entered")
    save_text(page, "6_password_entered")

    page.mouse.click(640, 590)
    page.wait_for_timeout(7000)
    take_shot(page, "7_home_page")
    save_text(page, "7_home_page")

    print("✅ Persistent session stored in 'login/' folder")
    browser.close()

def get_logged_in_page(p: Playwright, user_data_dir: Path):
    user_data_dir.mkdir(exist_ok=True)
    browser = p.chromium.launch_persistent_context(
        user_data_dir=str(user_data_dir),
        headless=True,
        viewport={"width": 1280, "height": 720}
    )
    page = browser.new_page()
    page.goto("https://twitter.com/home")

    if _is_logged_in(page):
        print("✅ Reused existing login from 'login/'")
        take_shot(page, "0_loaded_from_persistent")
        save_text(page, "0_loaded_from_persistent")
        return browser, page
    else:
        print("⚠️ Session not valid. Performing full login.")
        browser.close()
        _perform_full_login(p, user_data_dir)
        
        # Relaunch after login to get the fresh context
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=True,
            viewport={"width": 1280, "height": 720}
        )
        page = browser.new_page()
        page.goto("https://twitter.com/home")
        if not _is_logged_in(page):
             raise Exception("Failed to log in after performing full login procedure.")
        print("✅ Login successful, new session created.")
        return browser, page