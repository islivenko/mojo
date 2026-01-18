import os
from dotenv import load_dotenv
import bitrix_utils
import json

# --- Configuration ---
TARGET_SMART_PROCESS_ID = 1114
ITEM_ID_TO_DEBUG = 14

def main():
    """
    Fetches a single smart process item and prints its data for debugging.
    """
    # Load .env from the project root
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

    print(f"🚀 Fetching item ID {ITEM_ID_TO_DEBUG} from Smart Process ID {TARGET_SMART_PROCESS_ID}...")

    # The result from get_smart_item is already the 'item' dictionary
    item_data = bitrix_utils.get_smart_item(item_id=ITEM_ID_TO_DEBUG, entity_type_id=TARGET_SMART_PROCESS_ID)

    if not item_data:
        print("❌ Could not fetch the item. It might not exist or an API error occurred.")
        return

    print("\n--- Item Data from Bitrix24 API ---")
    print(json.dumps(item_data, indent=2, ensure_ascii=False))
    print("------------------------------------")

if __name__ == "__main__":
    main()
