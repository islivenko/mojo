import json
import os
from dotenv import load_dotenv
import bitrix_utils

# --- Configuration ---
SOURCE_DEAL_ID = 126
TARGET_SMART_PROCESS_ID = 1114
TARGET_ITEM_ID = 14

def main():
    """
    Fetches a source deal and a target smart process item and prints their data
    for comparison.
    """
    # Load .env from the project root
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

    print(f"🚀 Fetching source deal ID: {SOURCE_DEAL_ID}")
    deal_data = bitrix_utils.get_deal(SOURCE_DEAL_ID)
    if not deal_data:
        print("❌ Could not fetch the source deal.")
    else:
        print("\n--- Source Deal Data ---")
        print(json.dumps(deal_data, indent=2, ensure_ascii=False))
        print("------------------------")

    print(f"\n🚀 Fetching target item ID: {TARGET_ITEM_ID} from SP ID: {TARGET_SMART_PROCESS_ID}")
    item_data = bitrix_utils.get_smart_item(item_id=TARGET_ITEM_ID, entity_type_id=TARGET_SMART_PROCESS_ID)
    if not item_data:
        print("❌ Could not fetch the target item.")
    else:
        print("\n--- Target Smart Item Data ---")
        print(json.dumps(item_data, indent=2, ensure_ascii=False))
        print("------------------------------")

if __name__ == "__main__":
    main()
