import sys
import subprocess
import os

# --- Configuration ---
GENERATE_SCHEDULE_SCRIPT = "generate_schedule_file.py"
SCHEDULE_POSTS_RUNNER_SCRIPT = "schedule_posts_runner.py"

def run_script(script_name: str) -> bool:
    print(f"\n--- Running {script_name} ---")
    try:
        result = subprocess.run([sys.executable, script_name], check=True, capture_output=True, text=True)
        print(f"✅ {script_name} completed successfully.")
        print(f"--- Output from {script_name} ---")
        print(result.stdout)
        if result.stderr:
            print(f"--- Errors from {script_name} (if any) ---")
            print(result.stderr, file=sys.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {script_name} failed with exit code {e.returncode}.", file=sys.stderr)
        print(f"--- Output from {script_name} ---")
        print(e.stdout)
        if e.stderr:
            print(f"--- Errors from {script_name} ---")
            print(e.stderr, file=sys.stderr)
        return False
    except FileNotFoundError:
        print(f"❌ Error: Script '{script_name}' not found. Make sure it's in the same directory.", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred while running {script_name}: {e}", file=sys.stderr)
        return False

def main():
    print("--- Starting main workflow ---")

    # Step 1: Generate schedule file
    if not run_script(GENERATE_SCHEDULE_SCRIPT):
        print("‼️ Aborting workflow due to failure in schedule generation.", file=sys.stderr)
        sys.exit(1)

    # Step 2: Run the schedule posts runner (which handles login internally)
    if not run_script(SCHEDULE_POSTS_RUNNER_SCRIPT):
        print("‼️ Aborting workflow due to failure in post scheduling.", file=sys.stderr)
        sys.exit(1)

    print("\n--- Main workflow completed successfully. ---")

if __name__ == "__main__":
    main()