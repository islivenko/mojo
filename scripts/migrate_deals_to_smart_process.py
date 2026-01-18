import csv
import json
import os
from collections import defaultdict
from typing import Any, Dict, List

from dotenv import load_dotenv

import bitrix_utils

# --- Configuration ---
DEAL_CATEGORY_ID = "0"  # Deals from pipeline "Rekrutacja zewnętrzna"
TARGET_SMART_PROCESS_ID = 1114
SP_PROJEKT_ENTITY_TYPE_ID = 1098
MAP_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "deal_to_sp_map.csv")


def _format_projekt_value(value: str | None) -> str | None:
    if not value:
        return None
    try:
        projekt_id = int(value)
    except (TypeError, ValueError):
        return None
    return f"DYNAMIC_{SP_PROJEKT_ENTITY_TYPE_ID}_{projekt_id}"


def map_deal_to_smart_item_fields(deal: dict, contact: dict | None) -> Dict[str, Any]:
    fields: Dict[str, Any] = {
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
        fields["ufCrm42_1764709699969"] = str(deal.get("UF_CRM_1763403440"))
    elif deal.get("UF_CRM_1763403440"):
        fields["ufCrm42_1764709699969"] = str(deal.get("UF_CRM_1763403440"))

    if contact:
        fields["ufCrm42_1764519095692"] = contact.get("NAME")
        fields["ufCrm42_1764519115287"] = contact.get("LAST_NAME")
        fields["ufCrm42_1764520004789"] = contact.get("UF_CRM_1760983530268")

    return {k: v for k, v in fields.items() if v not in (None, "")}


def load_mapping() -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    if not os.path.exists(MAP_FILE_PATH):
        return mapping
    with open(MAP_FILE_PATH, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            deal_id = row.get("deal_id")
            item_id = row.get("smart_item_id")
            if deal_id and item_id:
                mapping[deal_id] = item_id
    return mapping


def save_mapping(mapping: Dict[str, str]) -> None:
    os.makedirs(os.path.dirname(MAP_FILE_PATH), exist_ok=True)
    with open(MAP_FILE_PATH, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["deal_id", "smart_item_id"])
        for deal_id, item_id in sorted(mapping.items(), key=lambda kv: int(kv[0])):
            writer.writerow([deal_id, item_id])


def fetch_deals() -> List[dict]:
    select = [
        "ID",
        "TITLE",
        "ASSIGNED_BY_ID",
        "DATE_CREATE",
        "CONTACT_ID",
        "UF_*",
    ]
    deals = bitrix_utils.list_deals(
        filter_params={"CATEGORY_ID": DEAL_CATEGORY_ID},
        select=select,
    )
    return deals


def fetch_contact(contact_id: str, cache: Dict[str, dict]) -> dict | None:
    if contact_id in cache:
        return cache[contact_id]
    contact = bitrix_utils.get_contact(int(contact_id)) if contact_id else None
    if contact:
        cache[contact_id] = contact
    return contact


def migrate_all_deals():
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

    mapping = load_mapping()
    deals = fetch_deals()
    contact_cache: Dict[str, dict] = {}

    stats = defaultdict(int)
    new_pairs: Dict[str, str] = {}

    print(f"🚀 Found {len(deals)} deals in category {DEAL_CATEGORY_ID}.")

    for deal in deals:
        deal_id = str(deal.get("ID"))
        if not deal_id:
            continue

        contact_id_raw = str(deal.get("CONTACT_ID") or "")
        contact = None
        if contact_id_raw and contact_id_raw != "0":
            contact = fetch_contact(contact_id_raw, contact_cache)
        fields = map_deal_to_smart_item_fields(deal, contact)

        if deal_id in mapping:
            item_id = mapping[deal_id]
            print(f"🔁 Updating existing smart item {item_id} from deal {deal_id} ...")
            result = bitrix_utils.update_smart_item(int(item_id), TARGET_SMART_PROCESS_ID, fields)
            if result and result.get("item"):
                stats["updated"] += 1
            else:
                stats["failed"] += 1
                print(f"   ❌ Update failed. Response: {result}")
        else:
            print(f"➕ Creating smart item for deal {deal_id} ...")
            result = bitrix_utils.create_smart_item(TARGET_SMART_PROCESS_ID, fields)
            if result and result.get("item"):
                item_id = str(result["item"].get("id"))
                mapping[deal_id] = item_id
                new_pairs[deal_id] = item_id
                stats["created"] += 1
                print(f"   ✅ Created smart item {item_id}")
            else:
                stats["failed"] += 1
                print(f"   ❌ Creation failed. Response: {result}")

    if new_pairs:
        save_mapping(mapping)
        print(f"💾 Mapping file updated with {len(new_pairs)} new pair(s).")
    else:
        print("ℹ️ Mapping unchanged.")

    print("\n--- Migration summary ---")
    print(f"Updated items: {stats['updated']}")
    print(f"Created items: {stats['created']}")
    print(f"Failed operations: {stats['failed']}")


if __name__ == "__main__":
    migrate_all_deals()
