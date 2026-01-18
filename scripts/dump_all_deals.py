import json
import os
from dotenv import load_dotenv
import bitrix_utils

# --- Configuration ---
OUTPUT_FILE = "scripts/output/all_deals_dump.json"

def main():
    """
    Fetches all deals from Bitrix24 and saves them to a single JSON file.
    """
    # Load .env from the project root
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

    print("🚀 Fetching all deals from Bitrix24...")

    # Fetch all deals with no filter
    all_deals = bitrix_utils.list_deals()

    if not all_deals:
        print("ℹ️ No deals found or an error occurred during fetching.")
        return

    print(f"✅ Successfully fetched {len(all_deals)} deals.")

    # Save the data to a file
    print(f"💾 Saving data to {OUTPUT_FILE}...")
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_deals, f, ensure_ascii=False, indent=4)
        print("✅ Done.")
    except IOError as e:
        print(f"❌ Error saving file: {e}")

if __name__ == "__main__":
    main()
