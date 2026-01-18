"""
Get SPA 1106 Structure from Bitrix24 API
Uses access token from Google Secret Manager

This script retrieves:
1. Entity type information for SPA 1106
2. All fields structure
3. Sample items to understand relationships
4. Related SPAs and their connections
"""

import os
import sys
import json
import requests
from google.cloud import secretmanager
from typing import Dict, Any, List

# Configuration
PROJECT_ID = "mojo-478621"
ACCESS_TOKEN_SECRET = "b24-access-token"
B24_DOMAIN = "mojo.bitrix24.pl"
SPA_1106_ID = 1106


class BitrixAPI:
    """Simple Bitrix24 API client with Secret Manager token"""

    def __init__(self, domain: str, project_id: str, access_token_secret: str):
        self.domain = domain
        self.base_url = f"https://{domain}/rest"
        self.project_id = project_id
        self.access_token_secret = access_token_secret
        self._access_token = None
        self._secret_client = None

    @property
    def secret_client(self):
        if self._secret_client is None:
            self._secret_client = secretmanager.SecretManagerServiceClient()
        return self._secret_client

    def get_access_token(self) -> str:
        """Get access token from Secret Manager"""
        if self._access_token:
            return self._access_token

        print(f"🔑 Fetching access token from Secret Manager...")
        secret_path = f"projects/{self.project_id}/secrets/{self.access_token_secret}/versions/latest"

        response = self.secret_client.access_secret_version(name=secret_path)
        self._access_token = response.payload.data.decode("UTF-8")
        print(f"✅ Access token retrieved")
        return self._access_token

    def call(self, method: str, params: Dict = None) -> Dict:
        """Make API call to Bitrix24"""
        url = f"{self.base_url}/{method}.json"
        params = params or {}
        params['auth'] = self.get_access_token()

        print(f"📤 API Request: {method}")

        try:
            response = requests.post(url, data=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if 'error' in data:
                error = data.get('error', 'Unknown error')
                error_desc = data.get('error_description', '')
                print(f"❌ API Error: {error} - {error_desc}")
                raise Exception(f"Bitrix24 API error: {error} - {error_desc}")

            print(f"✅ API Response received")
            return data.get('result', data)

        except requests.exceptions.RequestException as e:
            print(f"❌ API Request Failed: {e}")
            raise


def get_spa_1106_structure(api: BitrixAPI) -> Dict[str, Any]:
    """Get complete structure of SPA 1106"""

    print("\n" + "=" * 60)
    print("📋 GETTING SPA 1106 STRUCTURE")
    print("=" * 60 + "\n")

    structure = {}

    # 1. Get entity type info
    print("1️⃣ Getting entity type information...")
    entity_types = api.call('crm.type.list', {
        'filter[entityTypeId]': SPA_1106_ID
    })
    structure['entity_type'] = entity_types.get('types', [{}])[0] if entity_types.get('types') else {}
    print(f"   Entity: {structure['entity_type'].get('title', 'N/A')}")
    print(f"   ID: {structure['entity_type'].get('entityTypeId', 'N/A')}")

    # 2. Get all fields
    print("\n2️⃣ Getting fields structure...")
    fields_response = api.call('crm.item.fields', {
        'entityTypeId': SPA_1106_ID
    })
    structure['fields'] = fields_response.get('fields', {})

    # Analyze field types
    field_types = {}
    link_fields = []

    for field_name, field_info in structure['fields'].items():
        field_type = field_info.get('type', 'unknown')
        field_title = field_info.get('title', field_name)

        if field_type not in field_types:
            field_types[field_type] = []
        field_types[field_type].append(field_name)

        # Check for link fields (crm_entity, crm_contact, etc.)
        if 'crm' in field_type.lower() or field_name.startswith('ufCrm'):
            link_fields.append({
                'name': field_name,
                'title': field_title,
                'type': field_type,
                'settings': field_info.get('settings', {})
            })

    print(f"   Total fields: {len(structure['fields'])}")
    print(f"   Field types: {', '.join(f'{k}({len(v)})' for k, v in field_types.items())}")
    print(f"   Link fields found: {len(link_fields)}")

    structure['field_types'] = field_types
    structure['link_fields'] = link_fields

    # 3. Get sample items
    print("\n3️⃣ Getting sample items...")
    items_response = api.call('crm.item.list', {
        'entityTypeId': SPA_1106_ID,
        'select[0]': 'id',
        'select[1]': 'title',
        'select[2]': 'contactId',
        'select[3]': 'stageId',
        'order[id]': 'DESC'
    })
    structure['sample_items'] = items_response.get('items', [])
    print(f"   Found {len(structure['sample_items'])} items")

    # 4. Get detailed item (if exists)
    if structure['sample_items']:
        first_item_id = structure['sample_items'][0]['id']
        print(f"\n4️⃣ Getting detailed item (ID={first_item_id})...")

        item_response = api.call('crm.item.get', {
            'entityTypeId': SPA_1106_ID,
            'id': first_item_id
        })
        structure['detailed_item'] = item_response.get('item', {})

        # Analyze which fields have values
        filled_fields = []
        for field_name, field_value in structure['detailed_item'].items():
            if field_value and field_value != '' and field_value != []:
                filled_fields.append(field_name)

        print(f"   Filled fields: {len(filled_fields)}")
        structure['filled_fields'] = filled_fields

    return structure


def analyze_relationships(structure: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze relationships between SPA 1106 and other entities"""

    print("\n" + "=" * 60)
    print("🔗 ANALYZING RELATIONSHIPS")
    print("=" * 60 + "\n")

    relationships = {
        'contact': None,
        'linked_spas': [],
        'other_links': []
    }

    # Check for contact link
    if 'contactId' in structure.get('fields', {}):
        relationships['contact'] = {
            'field': 'contactId',
            'type': 'contact',
            'title': structure['fields']['contactId'].get('title', 'Contact')
        }
        print("✅ Contact link found: contactId")

    # Analyze link fields
    for link_field in structure.get('link_fields', []):
        field_name = link_field['name']
        field_title = link_field['title']
        field_type = link_field['type']
        settings = link_field.get('settings', {})

        print(f"\n🔗 Link field: {field_name}")
        print(f"   Title: {field_title}")
        print(f"   Type: {field_type}")

        # Check if it's a SPA link
        if 'entityTypeId' in settings:
            entity_type_id = settings['entityTypeId']
            relationships['linked_spas'].append({
                'field': field_name,
                'title': field_title,
                'entity_type_id': entity_type_id,
                'settings': settings
            })
            print(f"   → Links to SPA {entity_type_id}")
        else:
            relationships['other_links'].append({
                'field': field_name,
                'title': field_title,
                'type': field_type,
                'settings': settings
            })

    print(f"\n📊 Summary:")
    print(f"   Contact link: {'Yes' if relationships['contact'] else 'No'}")
    print(f"   Linked SPAs: {len(relationships['linked_spas'])}")
    print(f"   Other links: {len(relationships['other_links'])}")

    return relationships


def save_results(structure: Dict[str, Any], relationships: Dict[str, Any], output_dir: str = "output"):
    """Save results to JSON files"""

    print("\n" + "=" * 60)
    print("💾 SAVING RESULTS")
    print("=" * 60 + "\n")

    os.makedirs(output_dir, exist_ok=True)

    # Save full structure
    structure_file = f"{output_dir}/spa_1106_structure.json"
    with open(structure_file, 'w', encoding='utf-8') as f:
        json.dump(structure, f, indent=2, ensure_ascii=False)
    print(f"✅ Structure saved: {structure_file}")

    # Save relationships
    relationships_file = f"{output_dir}/spa_1106_relationships.json"
    with open(relationships_file, 'w', encoding='utf-8') as f:
        json.dump(relationships, f, indent=2, ensure_ascii=False)
    print(f"✅ Relationships saved: {relationships_file}")

    # Save summary
    summary = {
        'entity_type': structure.get('entity_type', {}),
        'total_fields': len(structure.get('fields', {})),
        'field_types': {k: len(v) for k, v in structure.get('field_types', {}).items()},
        'link_fields': structure.get('link_fields', []),
        'sample_items_count': len(structure.get('sample_items', [])),
        'relationships': relationships
    }

    summary_file = f"{output_dir}/spa_1106_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"✅ Summary saved: {summary_file}")


def print_summary(structure: Dict[str, Any], relationships: Dict[str, Any]):
    """Print human-readable summary"""

    print("\n" + "=" * 60)
    print("📊 SPA 1106 SUMMARY")
    print("=" * 60 + "\n")

    entity = structure.get('entity_type', {})
    print(f"Entity Type: {entity.get('title', 'N/A')}")
    print(f"Entity Type ID: {entity.get('entityTypeId', 'N/A')}")
    print(f"Code: {entity.get('code', 'N/A')}")
    print(f"Categories Enabled: {entity.get('isCategoriesEnabled', 'N/A')}")
    print(f"Stages Enabled: {entity.get('isStagesEnabled', 'N/A')}")

    print(f"\n📋 Fields:")
    print(f"   Total: {len(structure.get('fields', {}))}")
    for field_type, fields in structure.get('field_types', {}).items():
        print(f"   - {field_type}: {len(fields)}")

    print(f"\n🔗 Relationships:")
    if relationships.get('contact'):
        print(f"   ✅ Contact: {relationships['contact']['field']}")

    if relationships.get('linked_spas'):
        print(f"\n   📗 Linked SPAs ({len(relationships['linked_spas'])}):")
        for spa in relationships['linked_spas']:
            print(f"      - {spa['title']} (SPA {spa['entity_type_id']})")
            print(f"        Field: {spa['field']}")

    print(f"\n📦 Sample Items: {len(structure.get('sample_items', []))}")
    if structure.get('sample_items'):
        print(f"   Latest items:")
        for item in structure.get('sample_items', [])[:5]:
            print(f"   - ID {item.get('id')}: {item.get('title', 'N/A')}")


def main():
    """Main execution"""
    print("\n🚀 Starting SPA 1106 Structure Analysis\n")

    try:
        # Initialize API
        api = BitrixAPI(
            domain=B24_DOMAIN,
            project_id=PROJECT_ID,
            access_token_secret=ACCESS_TOKEN_SECRET
        )

        # Get structure
        structure = get_spa_1106_structure(api)

        # Analyze relationships
        relationships = analyze_relationships(structure)

        # Save results
        save_results(structure, relationships)

        # Print summary
        print_summary(structure, relationships)

        print("\n✅ Analysis completed successfully!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
