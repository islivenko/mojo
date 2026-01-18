import os
from dotenv import load_dotenv
import bitrix_utils
import json

# --- Configuration ---
TARGET_SMART_PROCESS_ID = 1114
TARGET_ITEM_ID = 14
FIELD_TO_UPDATE = "ufCrm42_1764517789771" # Projekt

# --- Data to Try ---
# Based on the URL, the 'Projekt' SP is type 1098 and the item ID is 40.
# Let's try the simplest possible format: just the integer ID.
VALUE_TO_SET = 40

def main():
    """
    Attempts to update a single field in a smart process item.
    """
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

    print(f"🚀 Attempting to update field '{FIELD_TO_UPDATE}' for Item ID {TARGET_ITEM_ID}...")
    print(f"   - Value to set: {VALUE_TO_SET}")

    fields_to_update = {
        FIELD_TO_UPDATE: VALUE_TO_SET
    }

    result = bitrix_utils.update_smart_item(
        item_id=TARGET_ITEM_ID,
        entity_type_id=TARGET_SMART_PROCESS_ID,
        fields=fields_to_update
    )

    if result and result.get("item"):
        print("   ✅ Update request sent successfully.")
    else:
        print(f"   ❌ Failed to send update request. Response: {result}")

if __name__ == "__main__":
    main()
