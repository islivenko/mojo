import json
import os
from dotenv import load_dotenv
import bitrix_utils

# --- Configuration ---
SOURCE_DEAL_ID = 120
TARGET_SMART_PROCESS_ID = 1114
SP_PROJEKT_ENTITY_TYPE_ID = 1098


def _format_projekt_value(value: str | None) -> str | None:
    if not value:
        return None
    try:
        projekt_id = int(value)
    except (TypeError, ValueError):
        return None
    return f"DYNAMIC_{SP_PROJEKT_ENTITY_TYPE_ID}_{projekt_id}"


def map_fields(deal: dict, contact: dict | None) -> dict:
    fields: dict[str, object] = {
        "title": deal.get("TITLE", "No Title"),
        "contact_id": deal.get("CONTACT_ID"),
        "assigned_by_id": deal.get("ASSIGNED_BY_ID"),
        "created_time": deal.get("DATE_CREATE"),
        "ufCrm42_1764517779308": deal.get("UF_CRM_1762177415680"),
        "ufCrm42_1764517789771": deal.get("UF_CRM_1762178348033"),
        "ufCrm42_1764517743442": deal.get("UF_CRM_1763324724062"),
    }

    projekt_value = _format_projekt_value(deal.get("UF_CRM_1763403440"))
    if projekt_value:
        fields["ufCrm42_1764517696"] = projekt_value
        fields[SYS_PROJEKT_FIELD] = str(deal.get("UF_CRM_1763403440"))
    elif deal.get("UF_CRM_1763403440"):
        fields[SYS_PROJEKT_FIELD] = str(deal.get("UF_CRM_1763403440"))

    if contact:
        fields["ufCrm42_1764519095692"] = contact.get("NAME")
        fields["ufCrm42_1764519115287"] = contact.get("LAST_NAME")
        fields["ufCrm42_1764520004789"] = contact.get("UF_CRM_1760983530268")

    return {k: v for k, v in fields.items() if v not in (None, "")}


def main():
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

    print(f"🚀 Migrating deal ID {SOURCE_DEAL_ID} to smart process {TARGET_SMART_PROCESS_ID}...")
    deal = bitrix_utils.get_deal(SOURCE_DEAL_ID)
    if not deal:
        print("❌ Deal not found")
        return

    contact = None
    if deal.get("CONTACT_ID"):
        contact = bitrix_utils.get_contact(int(deal["CONTACT_ID"]))

    fields = map_fields(deal, contact)
    print("   - Fields to send:")
    print(json.dumps(fields, indent=2, ensure_ascii=False))

    result = bitrix_utils.create_smart_item(
        entity_type_id=TARGET_SMART_PROCESS_ID,
        fields=fields
    )

    if result and result.get("item"):
        item_id = result["item"].get("id")
        print(f"✅ Smart process item created with ID {item_id}")
    else:
        print(f"❌ Creation failed. Response: {result}")


if __name__ == "__main__":
    main()
