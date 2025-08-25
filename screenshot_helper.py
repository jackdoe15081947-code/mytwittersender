import os
from pathlib import Path
from datetime import datetime
from playwright.sync_api import Page

# --- Configuration ---
SCREENSHOT_DIR = Path("./screenshots")
current_log_dir = None

def start_new_log():
    """Initializes a new directory for a sequence of screenshots."""
    global current_log_dir
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_log_dir = SCREENSHOT_DIR / f"log_{timestamp}"
    current_log_dir.mkdir(parents=True, exist_ok=True)
    print(f"📸 Started new screenshot log at: {current_log_dir}")

def log_action(page: Page, action_name: str):
    """Takes a screenshot and saves it with an action name."""
    if current_log_dir is None:
        start_new_log() # Automatically start if not already
    
    timestamp = datetime.now().strftime("%H%M%S_%f")[:-3] # HHMMSS_ms
    filename = current_log_dir / f"{timestamp}_{action_name}.png"
    try:
        page.screenshot(path=str(filename))
        # print(f"   -> Screenshot: {filename.name}")
    except Exception as e:
        print(f"⚠️ Warning: Could not take screenshot for '{action_name}': {e}", file=sys.stderr)