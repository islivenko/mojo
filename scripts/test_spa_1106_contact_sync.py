"""
Test Contact Fields Sync for SPA 1106
Tests syncing passport fields from Contact to Sprawy cudzoziemców
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'google-cloud', 'b24-spa-1106-sync', 'b24-spa-1106-sync-worker'))

from services.bitrix_api import BitrixAPI
from services.contact_sync import ContactFieldsSyncService
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configuration
PROJECT_ID = "mojo-478621"
ACCESS_TOKEN_SECRET = "b24-access-token"
B24_DOMAIN = "mojo.bitrix24.pl"
SPA_1106_ID = 1106

# Test data
TEST_CONTACT_ID = 194
TEST_SPRAWY_ID = 18

def main():
    print("\n" + "=" * 60)
    print("🧪 TEST: Contact Fields Sync for SPA 1106")
    print("=" * 60 + "\n")
    
    # Initialize API
    print("🔧 Initializing Bitrix24 API...")
    api = BitrixAPI(
        domain=B24_DOMAIN,
        project_id=PROJECT_ID,
        access_token_secret=ACCESS_TOKEN_SECRET
    )
    
    # Initialize sync service
    print("🔧 Initializing Contact Sync Service...")
    sync_service = ContactFieldsSyncService(
        bitrix=api,
        spa_sprawy=SPA_1106_ID
    )
    
    print("\n" + "=" * 60)
    print("📋 TEST 1: Get Contact Data")
    print("=" * 60 + "\n")
    
    contact = api.get_contact(TEST_CONTACT_ID)
    print(f"Contact ID: {TEST_CONTACT_ID}")
    print(f"Name: {contact.get('NAME')} {contact.get('LAST_NAME')}")
    print(f"Numer paszportu: {contact.get('UF_CRM_1758997725285')}")
    print(f"Data ważności: {contact.get('UF_CRM_1760984058065')}")
    print(f"Data urodzin: {contact.get('BIRTHDATE')}")
    
    print("\n" + "=" * 60)
    print("📋 TEST 2: Get Sprawy Data (Before Sync)")
    print("=" * 60 + "\n")
    
    sprawy = api.get_item(SPA_1106_ID, TEST_SPRAWY_ID)
    print(f"Sprawy ID: {TEST_SPRAWY_ID}")
    print(f"Title: {sprawy.get('title')}")
    print(f"Contact ID: {sprawy.get('contactId')}")
    print(f"nr paszportu: {sprawy.get('ufCrm38_1764509760429')}")
    print(f"Data ważności paszportu: {sprawy.get('ufCrm38_1764509780038')}")
    print(f"Data urodzin: {sprawy.get('ufCrm38_1768738050')}")
    print(f"Nazwisko imię: {sprawy.get('ufCrm38_1768738005')}")
    
    print("\n" + "=" * 60)
    print("📋 TEST 3: Sync Contact → Sprawy")
    print("=" * 60 + "\n")
    
    result = sync_service.sync_fields_to_sprawy(
        sprawy_id=TEST_SPRAWY_ID,
        contact_id=TEST_CONTACT_ID
    )
    
    print(f"\nSync Result:")
    print(f"  Action: {result.get('action')}")
    if result.get('updated_fields'):
        print(f"  Updated fields:")
        for field, value in result.get('updated_fields', {}).items():
            print(f"    - {field}: {value}")
    
    print("\n" + "=" * 60)
    print("📋 TEST 4: Get Sprawy Data (After Sync)")
    print("=" * 60 + "\n")
    
    sprawy_after = api.get_item(SPA_1106_ID, TEST_SPRAWY_ID)
    print(f"Sprawy ID: {TEST_SPRAWY_ID}")
    print(f"Title: {sprawy_after.get('title')}")
    print(f"nr paszportu: {sprawy_after.get('ufCrm38_1764509760429')}")
    print(f"Data ważności paszportu: {sprawy_after.get('ufCrm38_1764509780038')}")
    print(f"Data urodzin: {sprawy_after.get('ufCrm38_1768738050')}")
    print(f"Nazwisko imię: {sprawy_after.get('ufCrm38_1768738005')}")
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETED")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
