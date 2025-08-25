# new_stuff/common/screenshot_helper.py

from pathlib import Path
from playwright.sync_api import Page

# --- Configuration ---
# All screenshots will be saved in a new 'screenshots' folder.
SCREENSHOT_DIR = Path("./screenshots")
_STEP_COUNTER = 1

def start_new_log():
    """
    Resets the step counter. Call this function once before processing each new tweet.
    This is the key to overwriting the previous post's logs.
    """
    global _STEP_COUNTER
    _STEP_COUNTER = 1
    # Also ensures the screenshot directory exists at the start of each new log.
    SCREENSHOT_DIR.mkdir(exist_ok=True)

def log_action(page: Page, action_name: str):
    """
    Takes a screenshot with a numbered filename based on the current step.
    e.g., '1_click_textarea.png', '2_fill_text.png', etc.
    """
    global _STEP_COUNTER
    # Create the filename using the current step number.
    filename = f"{_STEP_COUNTER}_{action_name}.png"
    
    try:
        page.screenshot(path=SCREENSHOT_DIR / filename)
        print(f"   📸 Screenshot saved: {filename}")
    except Exception as e:
        print(f"   ⚠️ Could not save screenshot for action '{action_name}': {e}")
    
    # Increment the counter for the next step.
    _STEP_COUNTER += 1
