import os
import json

import bitrix_utils

# --- Configuration ---
OUTPUT_DIR = "output"
SMART_PROCESS_ID = 1114  # As per https://mojo.bitrix24.pl/page/rekrutacja/sprawy_rekrutacyjne/

def main():
    """
    Fetches field definitions for Deals, Contacts, and a specific Smart Process
    and saves them to JSON files.
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print("\nFetching Deal fields...")
    deal_fields = bitrix_utils.get_deal_fields()
    if deal_fields:
        with open(os.path.join(OUTPUT_DIR, "deal_fields.json"), "w", encoding="utf-8") as f:
            json.dump(deal_fields, f, ensure_ascii=False, indent=4)
        print("✅ Saved deal fields to output/deal_fields.json")

    print("\nFetching Contact fields...")
    contact_fields = bitrix_utils.get_contact_fields()
    if contact_fields:
        with open(os.path.join(OUTPUT_DIR, "contact_fields.json"), "w", encoding="utf-8") as f:
            json.dump(contact_fields, f, ensure_ascii=False, indent=4)
        print("✅ Saved contact fields to output/contact_fields.json")

    print(f"\nFetching Smart Process fields for entity ID {SMART_PROCESS_ID}...")
    sp_fields = bitrix_utils.get_all_smart_process_fields(SMART_PROCESS_ID)
    if sp_fields:
        filename = f"smart_process_{SMART_PROCESS_ID}_fields.json"
        with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
            json.dump(sp_fields, f, ensure_ascii=False, indent=4)
        print(f"✅ Saved smart process fields to output/{filename}")

if __name__ == "__main__":
    main()
