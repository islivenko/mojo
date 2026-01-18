import os
import sys
import json
from dotenv import load_dotenv

sys.path.append(os.path.dirname(__file__))
import bitrix_utils

ITEM_ID = 16
ENTITY_TYPE_ID = 1114


def main():
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

    print(f"🚀 Reading smart process item {ITEM_ID}...")
    payload = bitrix_utils._make_bitrix_api_call(
        "crm.item.get",
        {
            "entityTypeId": ENTITY_TYPE_ID,
            "id": ITEM_ID,
            "select": ["*", "UF_*"]
        },
        auth=None,
        http_method="POST",
        unwrap_result=False,
    )

    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
