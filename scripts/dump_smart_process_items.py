import json
import os
from dotenv import load_dotenv
import bitrix_utils

# --- Configuration ---
SMART_PROCESS_ID = 1114
OUTPUT_FILE = f"scripts/output/smart_process_{SMART_PROCESS_ID}_items_dump.json"

def main():
    """
    Fetches all items from a specific smart process and saves them to a JSON file.
    """
    # Load .env from the project root
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

    print(f"🚀 Fetching all items from Smart Process ID {SMART_PROCESS_ID}...")

    # Fetch all items with no filter
    all_items = bitrix_utils.list_smart_items(entity_type_id=SMART_PROCESS_ID)

    if not all_items:
        print("ℹ️ No items found in this smart process or an error occurred.")
        return

    print(f"✅ Successfully fetched {len(all_items)} items.")

    # Save the data to a file
    print(f"💾 Saving data to {OUTPUT_FILE}...")
    try:
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_items, f, ensure_ascii=False, indent=4)
        print("✅ Done.")
    except IOError as e:
        print(f"❌ Error saving file: {e}")

if __name__ == "__main__":
    main()
