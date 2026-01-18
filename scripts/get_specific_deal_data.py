import json
import os
from dotenv import load_dotenv
import bitrix_utils

# --- Configuration ---
SOURCE_DEAL_ID = 126

def main():
    """
    Fetches specific fields from a single deal and prints them.
    """
    # Load .env from the project root
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

    print(f"🚀 Fetching data for Deal ID: {SOURCE_DEAL_ID}")
    # The get_deal function should return all fields, including custom ones
    deal_data = bitrix_utils.get_deal(SOURCE_DEAL_ID)

    if not deal_data:
        print("❌ Could not fetch the deal.")
        return

    print("\n--- Field Values from Source Deal ---")
    print(f"Projekt (UF_CRM_1763403440): {deal_data.get('UF_CRM_1763403440')}")
    print(f"Data BHP (UF_CRM_1762177415680): {deal_data.get('UF_CRM_1762177415680')}")
    print(f"Data przyjazdu na mieszkanie (UF_CRM_1762178348033): {deal_data.get('UF_CRM_1762178348033')}")
    print(f"Freelancer (UF_CRM_1763324724062): {deal_data.get('UF_CRM_1763324724062')}")
    print("-------------------------------------")

if __name__ == "__main__":
    main()
