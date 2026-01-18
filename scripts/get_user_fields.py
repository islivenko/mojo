import json
import os
import argparse
from dotenv import load_dotenv
import bitrix_utils

def main():
    """
    Fetches user fields for a specified CRM entity ID and saves them to a JSON file.
    """
    parser = argparse.ArgumentParser(description="Fetch Bitrix24 user fields for a CRM entity.")
    parser.add_argument("entity_id", type=str, help="The CRM entity ID (e.g., CRM_DEAL, CRM_CONTACT, CRM_1114).")
    args = parser.parse_args()

    # Load .env from the project root
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

    print(f"🚀 Fetching user fields for entity: {args.entity_id}...")

    # We need a new function in bitrix_utils for this
    user_fields = bitrix_utils.list_user_fields(args.entity_id)

    if not user_fields:
        print(f"ℹ️ No user fields found for entity {args.entity_id} or an error occurred.")
        return

    print(f"✅ Successfully fetched {len(user_fields)} user fields.")

    # Prepare filename
    sanitized_entity_id = args.entity_id.lower().replace("_", "")
    output_file = f"scripts/output/{sanitized_entity_id}_user_fields.json"

    # Save the data to a file
    print(f"💾 Saving data to {output_file}...")
    try:
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(user_fields, f, ensure_ascii=False, indent=4)
        print("✅ Done.")
    except IOError as e:
        print(f"❌ Error saving file: {e}")

if __name__ == "__main__":
    main()
