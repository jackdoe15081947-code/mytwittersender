import os
import sys
import subprocess
import json
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from pathlib import Path

load_dotenv()

# --- Configuration ---
BOT_CATEGORIES = ["formula", "tech", "hollywood", "movies", "unews", "news"]
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DATA_LIST_DIR = Path("./data_list")
POST_NOW_THRESHOLD_MINUTES = 5

def fetch_data(supabase: Client):
    """Fetches all data directly from the 'to_process' table."""
    print("Attempting to fetch data from 'to_process'...")
    try:
        # The 'post_at' column should be a 'timestamp with time zone' type in Supabase
        response = supabase.table("to_process").select("*").execute()
        if response.data:
            print(f"✅ Fetched {len(response.data)} rows from 'to_process'.")
            return response.data
        else:
            print("ℹ️ 'to_process' table is empty.")
            return []
    except Exception as e:
        print(f"❌ An error occurred fetching from Supabase: {e}", file=sys.stderr)
        return []

def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        sys.exit("❌ Error: Supabase environment variables not set.")

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    all_data = fetch_data(supabase)

    if not all_data:
        print("No data to process. Exiting gracefully.")
        sys.exit(0)

    # --- Data Preparation and Sorting ---
    print("\n--- Preparing and Sorting Data ---")
    current_time = datetime.now(timezone.utc) # Use timezone-aware current time for comparison
    post_now_threshold = current_time + timedelta(minutes=POST_NOW_THRESHOLD_MINUTES)
    print(f"Reference Time (UTC): {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    categorized_data = {bot: {"post_now": [], "schedule": []} for bot in BOT_CATEGORIES}

    for row in all_data:
        bot_tag = row.get("bot")
        post_at_str = row.get("time") # Assuming column is named 'post_at'

        if not all([bot_tag, post_at_str, row.get("title"), row.get("url")]):
            print(f"⚠️ Warning: Skipping row due to missing data: {row}", file=sys.stderr)
            continue
        
        if bot_tag not in BOT_CATEGORIES:
            print(f"⚠️ Warning: Skipping row with unknown bot category '{bot_tag}': {row}", file=sys.stderr)
            continue

        # Convert the ISO format string from Supabase into a timezone-aware datetime object
        try:
            item_datetime = datetime.fromisoformat(post_at_str)
        except (ValueError, TypeError):
            print(f"⚠️ Warning: Could not parse datetime '{post_at_str}'. Skipping row.", file=sys.stderr)
            continue
            
        # Sort into 'post_now' or 'schedule' list
        if item_datetime <= post_now_threshold:
            categorized_data[bot_tag]["post_now"].append(row)
        else:
            categorized_data[bot_tag]["schedule"].append(row)

    print("✅ Data sorting complete.")

    # --- Debugging Step: Write Sorted Data to Files ---
    print("\n--- Writing sorted data to debug files ---")
    DATA_LIST_DIR.mkdir(exist_ok=True)
    for category, data in categorized_data.items():
        if data["post_now"] or data["schedule"]:
            file_path = DATA_LIST_DIR / f"{category}.txt"
            try:
                with open(file_path, 'w') as f:
                    # The 'post_at' field will be saved in its original string format
                    json.dump(data, f, indent=4)
                print(f"   -> Saved debug file: {file_path}")
            except IOError as e:
                print(f"   ❌ Error writing debug file for {category}: {e}", file=sys.stderr)

    # --- Bot Processing Loop ---
    print("\n--- Starting Bot Processing Loop ---")
    for category in BOT_CATEGORIES:
        data_for_bot = categorized_data[category]
        if not data_for_bot["post_now"] and not data_for_bot["schedule"]:
            continue

        print(f"\n--- Processing category: {category} ---")
        process_script_path = os.path.join("bot", "process_bot.py")

        try:
            # Setup environment variables for the subprocess
            proc_env = os.environ.copy()
            proc_env["TWITTER_EMAIL"] = os.getenv(f"{category.upper()}_EMAIL")
            proc_env["TWITTER_USERNAME"] = os.getenv(f"{category.upper()}_USERNAME")
            proc_env["TWITTER_PASSWORD"] = os.getenv(f"{category.upper()}_PASSWORD")
            proc_env["BOT_CATEGORY"] = category

            if not all([proc_env["TWITTER_EMAIL"], proc_env["TWITTER_USERNAME"], proc_env["TWITTER_PASSWORD"]]):
                print(f"⚠️ Warning: Missing secrets for {category.upper()}. Skipping.")
                continue

            # Pass the pre-sorted data as a JSON string
            data_to_pass_json = json.dumps(data_for_bot)
            
            print(f"Executing bot process for '{category}'...")
            subprocess.run(
                [sys.executable, process_script_path, data_to_pass_json], 
                check=True, env=proc_env
            )
            print(f"✅ Bot process completed for '{category}'.")

        except subprocess.CalledProcessError:
            print(f"❌ An error occurred while processing category '{category}'.", file=sys.stderr)
            continue

    print("\n--- Workflow finished ---")

if __name__ == "__main__":
    main()
