"""Get SPA 1042 (Podstawy pobytu) structure"""
import sys
import json
sys.path.insert(0, '../google-cloud/b24-spa-1106-sync/b24-spa-1106-sync-worker')
from services.bitrix_api import BitrixAPI

bitrix = BitrixAPI(
    domain='mojo.bitrix24.pl',
    project_id='mojo-478621',
    access_token_secret='b24-access-token'
)

# Get field structure
import requests
url = 'https://mojo.bitrix24.pl/rest/crm.type.fields'
params = {'entityTypeId': 1042}

response = bitrix._make_request('POST', url, json=params)
fields = response.get('fields', {})

print('=== Podstawy pobytu (1042) - All fields ===')
print()

# Filter date fields
date_fields = {}
for field_name, field_info in fields.items():
    if field_info.get('type') == 'date':
        date_fields[field_name] = field_info
        print(f"{field_name}:")
        print(f"  Title: {field_info.get('title')}")
        print(f"  Type: {field_info.get('type')}")
        print(f"  Multiple: {field_info.get('isMultiple', False)}")
        print(f"  Upper Name: {field_info.get('upperName', '')}")
        print()

# Save to file
with open('output/spa_1042_date_fields.json', 'w') as f:
    json.dump(date_fields, f, indent=2, ensure_ascii=False)

print(f"\n✅ Found {len(date_fields)} date fields")
print(f"📁 Saved to output/spa_1042_date_fields.json")
