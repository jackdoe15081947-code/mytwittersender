import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

# --- Configuration ---
POSTS_FILE = Path("./posts.json")
SCHEDULE_OUTPUT_FILE = Path("./schedule.json")

# Scheduling time window (UTC)
SCHEDULE_WINDOW_START_HOUR = 3
SCHEDULE_WINDOW_START_MINUTE = 30
SCHEDULE_WINDOW_END_HOUR = 11
SCHEDULE_WINDOW_END_MINUTE = 30

# --- Schedule Generation Logic ---
def generate_schedule(posts_data: list) -> list:
    print("\n--- Generating schedule ---")
    
    # Get today's date in UTC, set to midnight
    today_utc = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    generated_posts = []

    hourly_entries = [p for p in posts_data if p.get("time") == "hourly"]
    other_entries = [p for p in posts_data if p.get("time") != "hourly"]

    # Track offset for hourly posts
    hourly_post_index_counter = 0

    # Process hourly entries first
    for entry in hourly_entries:
        # Calculate initial minute offset (30, 40, 50, 0, 10, 20...)
        initial_minute_offset = SCHEDULE_WINDOW_START_MINUTE + (hourly_post_index_counter % 6) * 10
        # Calculate initial hour shift (0 for first 6, 1 for next 6, etc.)
        initial_hour_shift = (hourly_post_index_counter // 6) 

        current_hour_in_window = SCHEDULE_WINDOW_START_HOUR
        
        while True:
            # Calculate the actual scheduled hour and minute for this iteration
            scheduled_hour = current_hour_in_window + initial_hour_shift
            scheduled_minute = initial_minute_offset

            # Handle minute overflow
            if scheduled_minute >= 60:
                scheduled_hour += scheduled_minute // 60
                scheduled_minute %= 60
            
            # Create the datetime object for this potential post
            current_scheduled_time = today_utc.replace(
                hour=scheduled_hour,
                minute=scheduled_minute,
                second=0, microsecond=0
            )

            # Define the exact window boundaries for comparison
            window_start_dt = today_utc.replace(
                hour=SCHEDULE_WINDOW_START_HOUR, 
                minute=SCHEDULE_WINDOW_START_MINUTE,
                second=0, microsecond=0
            )
            window_end_dt = today_utc.replace(
                hour=SCHEDULE_WINDOW_END_HOUR, 
                minute=SCHEDULE_WINDOW_END_MINUTE,
                second=0, microsecond=0
            )
            
            # Check if this generated time is within the allowed window
            if window_start_dt <= current_scheduled_time <= window_end_dt:
                generated_posts.append({
                    "title": entry["title"],
                    "timestamp": current_scheduled_time.isoformat()
                })
            elif current_scheduled_time > window_end_dt:
                # If we've passed the end of the window, stop generating for this hourly entry
                break
            
            # Move to the next hour for generating posts
            current_hour_in_window += 1
            # Safety break for the loop
            if current_hour_in_window > SCHEDULE_WINDOW_END_HOUR + initial_hour_shift + 10: # Add a larger buffer for safety
                 break

        hourly_post_index_counter += 1

    # Process other entries (quarterly and specific times)
    for entry in other_entries:
        time_str = entry["time"]
        if time_str == "quarterly":
            quarterly_times = [
                today_utc.replace(hour=3, minute=30, second=0, microsecond=0), # 3:30 AM UTC
                today_utc.replace(hour=6, minute=30, second=0, microsecond=0), # 6:30 AM UTC
                today_utc.replace(hour=9, minute=30, second=0, microsecond=0), # 9:30 AM UTC
                today_utc.replace(hour=11, minute=30, second=0, microsecond=0) # 11:30 AM UTC
            ]
            for q_time in quarterly_times:
                generated_posts.append({
                    "title": entry["title"],
                    "timestamp": q_time.isoformat()
                })
        else: # Specific time
            try:
                # Parse specific time, assuming format like "H:MM AM/PM" or "HH:MM"
                try:
                    parsed_time = datetime.strptime(time_str, "%I:%M %p").time()
                except ValueError:
                    parsed_time = datetime.strptime(time_str, "%H:%M").time()
                
                specific_datetime_utc = today_utc.replace(
                    hour=parsed_time.hour,
                    minute=parsed_time.minute,
                    second=0, microsecond=0
                )
                generated_posts.append({
                    "title": entry["title"],
                    "timestamp": specific_datetime_utc.isoformat()
                })
            except ValueError:
                print(f"⚠️ Warning: Could not parse specific time '{time_str}'. Skipping entry: {entry}")
                continue
    
    # Sort posts by timestamp
    generated_posts.sort(key=lambda x: x["timestamp"])

    print(f"✅ Generated {len(generated_posts)} posts.")
    return generated_posts

# --- Main function for this script ---
def main():
    # Read posts.json
    if not POSTS_FILE.exists():
        print(f"❌ Error: {POSTS_FILE} not found. Please create it.")
        exit(1)
    try:
        with open(POSTS_FILE, 'r', encoding='utf-8') as f:
            posts_data = json.load(f)
        print(f"✅ Loaded {len(posts_data)} entries from {POSTS_FILE}.")
    except json.JSONDecodeError as e:
        print(f"❌ Error decoding JSON from {POSTS_FILE}: {e}")
        exit(1)
    except Exception as e:
        print(f"❌ Error reading {POSTS_FILE}: {e}")
        exit(1)

    # Generate the schedule
    scheduled_items = generate_schedule(posts_data)

    # Write schedule.json
    try:
        with open(SCHEDULE_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(scheduled_items, f, indent=4)
        print(f"✅ Schedule written to {SCHEDULE_OUTPUT_FILE}.")
    except IOError as e:
        print(f"❌ Error writing {SCHEDULE_OUTPUT_FILE}: {e}")
        exit(1)

if __name__ == "__main__":
    main()