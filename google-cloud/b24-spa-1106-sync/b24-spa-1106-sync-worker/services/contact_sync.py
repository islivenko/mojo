"""
Contact Fields Sync: Contact → Sprawy cudzoziemców (SPA 1106)

Synchronizes passport fields from Contact to all linked Sprawy.

Current field mappings:
- Contact.UF_CRM_1758997725285 (Numer paszportu) → Sprawy.ufCrm38_1764509760429 (nr paszportu)
- Contact.UF_CRM_1760984058065 (Data ważności) → Sprawy.ufCrm38_1764509780038 (Data ważności paszportu)

Flow:
1. On Contact update (ONCRMCONTACTUPDATE):
   - Find all Sprawy (SPA 1106) linked to this contact
   - Copy passport fields from Contact to each Sprawy

2. On Sprawy create/update (ONCRMDYNAMICITEMADD/UPDATE for 1106):
   - Get contact_id from Sprawy
   - Copy passport fields from Contact to Sprawy

Extensible: Add more fields to FIELD_MAPPINGS as needed.
"""

import logging
from typing import Optional, Dict, List, Any

from .bitrix_api import BitrixAPI

logger = logging.getLogger('b24-sync')


# Field mappings: Contact field → Sprawy field
# Supports:
#   - Single field: "contact_field": "FIELD_NAME"
#   - Combined fields: "contact_fields": ["FIELD1", "FIELD2"], "format": "{0} {1}"
FIELD_MAPPINGS = [
    {
        "name": "Numer paszportu",
        "contact_field": "UF_CRM_1758997725285",
        "sprawy_field": "ufCrm38_1764509760429"
    },
    {
        "name": "Data ważności paszportu",
        "contact_field": "UF_CRM_1760984058065",
        "sprawy_field": "ufCrm38_1764509780038"
    },
]

# Title format for Sprawy (uses Contact fields + Sprawy ID)
# Format: {LAST_NAME} {NAME} • Sprawa nr. {ID}
# Example: DARAI BISHNU LAL • Sprawa nr. 18
TITLE_CONFIG = {
    "enabled": False,  # Disabled - title is managed manually
    "contact_fields": ["LAST_NAME", "NAME"],
    "format": "{last_name} {name} • Sprawa nr. {id}"
}


class ContactFieldsSyncService:
    """Service for syncing field values from Contact to Sprawy."""

    def __init__(
        self,
        bitrix: BitrixAPI,
        spa_sprawy: int = 1106,
        field_mappings: List[Dict] = None
    ):
        """
        Initialize contact fields sync service.

        Args:
            bitrix: Bitrix24 API client
            spa_sprawy: Entity type ID for Sprawy SPA (1106)
            field_mappings: List of field mappings (uses FIELD_MAPPINGS if not provided)
        """
        self.bitrix = bitrix
        self.spa_sprawy = spa_sprawy
        self.field_mappings = field_mappings or FIELD_MAPPINGS

        self.title_config = TITLE_CONFIG

        logger.info(f"🔧 ContactFieldsSyncService initialized:")
        logger.info(f"   📗 Sprawy SPA: {spa_sprawy}")
        logger.info(f"   📋 Field mappings: {len(self.field_mappings)}")
        for mapping in self.field_mappings:
            if 'contact_fields' in mapping:
                fields_str = '+'.join(mapping['contact_fields'])
                logger.info(f"      - {mapping['name']}: Contact.[{fields_str}] → Sprawy.{mapping['sprawy_field']}")
            else:
                logger.info(f"      - {mapping['name']}: Contact.{mapping['contact_field']} → Sprawy.{mapping['sprawy_field']}")
        if self.title_config.get('enabled'):
            logger.info(f"   🏷️ Title sync: {self.title_config['format']}")

    def _get_contact_fields(self, contact_id: int) -> Dict[str, Any]:
        """
        Get mapped field values from Contact.

        Supports:
        - Single field mapping: {"contact_field": "FIELD_NAME"}
        - Combined fields: {"contact_fields": ["F1", "F2"], "format": "{0} {1}"}

        Args:
            contact_id: Contact ID

        Returns:
            Dict with sprawy_field → value mappings
        """
        logger.info(f"👤 Fetching Contact ID={contact_id}...")

        contact = self.bitrix.get_contact(contact_id)

        # Build result mapping
        result = {}
        for mapping in self.field_mappings:
            sprawy_field = mapping['sprawy_field']
            name = mapping['name']

            if 'contact_fields' in mapping:
                # Combined fields: join multiple fields using format string
                fields = mapping['contact_fields']
                format_str = mapping.get('format', ' '.join(['{' + str(i) + '}' for i in range(len(fields))]))
                values = [contact.get(f, '') or '' for f in fields]
                value = format_str.format(*values).strip()
                logger.info(f"   📋 {name}: {fields} → '{value}'")
            else:
                # Single field mapping
                contact_field = mapping['contact_field']
                value = contact.get(contact_field, '') or ''
                logger.info(f"   📋 {name}: '{value}'")

            result[sprawy_field] = value

        return result

    def _generate_title(self, contact: Dict, sprawy_id: int) -> Optional[str]:
        """
        Generate title for Sprawy based on Contact fields and ID.

        Format: {LAST_NAME} {NAME} • Sprawa nr. {ID}
        Example: DALAKISHVILI VAKHTANH • Sprawa nr. 10

        Args:
            contact: Contact data dict
            sprawy_id: Sprawy element ID

        Returns:
            Generated title string or None if title sync disabled
        """
        if not self.title_config.get('enabled'):
            return None

        last_name = contact.get('LAST_NAME', '') or ''
        name = contact.get('NAME', '') or ''

        title = self.title_config['format'].format(
            last_name=last_name,
            name=name,
            id=sprawy_id
        ).strip()

        logger.info(f"   🏷️ Generated title: '{title}'")
        return title

    def sync_fields_to_sprawy(
        self,
        sprawy_id: int,
        contact_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Sync field values from Contact to a specific Sprawy.

        Called when Sprawy is created/updated.

        Args:
            sprawy_id: Sprawy element ID
            contact_id: Contact ID (optional, will fetch from Sprawy if not provided)

        Returns:
            Sync result with details
        """
        logger.info("=" * 50)
        logger.info(f"🔄 SYNC FIELDS: Contact → Sprawy ID={sprawy_id}")
        logger.info("=" * 50)

        # Step 1: Get Sprawy to find contact_id if not provided
        if not contact_id:
            logger.info(f"📗 Step 1: Fetching Sprawy ID={sprawy_id} to get contactId...")
            sprawy = self.bitrix.get_item(self.spa_sprawy, sprawy_id)
            contact_id = sprawy.get('contactId')

            if not contact_id:
                logger.warning(f"⚠️ Sprawy {sprawy_id} has no contactId - skipping")
                return {
                    "action": "skipped",
                    "reason": "No contactId in Sprawy",
                    "sprawy_id": sprawy_id
                }
        else:
            logger.info(f"📗 Step 1: Using provided contact_id={contact_id}")

        # Step 2: Get field values from Contact + generate title
        logger.info(f"👤 Step 2: Getting field values from Contact ID={contact_id}...")
        try:
            # Get contact for both fields and title generation
            contact = self.bitrix.get_contact(contact_id)

            # Get field mappings
            field_values = {}
            for mapping in self.field_mappings:
                sprawy_field = mapping['sprawy_field']
                name = mapping['name']

                if 'contact_fields' in mapping:
                    fields = mapping['contact_fields']
                    format_str = mapping.get('format', ' '.join(['{' + str(i) + '}' for i in range(len(fields))]))
                    values = [contact.get(f, '') or '' for f in fields]
                    value = format_str.format(*values).strip()
                    logger.info(f"   📋 {name}: {fields} → '{value}'")
                else:
                    contact_field = mapping['contact_field']
                    value = contact.get(contact_field, '') or ''
                    logger.info(f"   📋 {name}: '{value}'")

                field_values[sprawy_field] = value

            # Generate title
            title = self._generate_title(contact, sprawy_id)
            if title:
                field_values['title'] = title

        except Exception as e:
            logger.error(f"❌ Failed to get Contact {contact_id}: {e}")
            return {
                "action": "error",
                "reason": f"Failed to get Contact: {e}",
                "sprawy_id": sprawy_id,
                "contact_id": contact_id
            }

        if not field_values:
            logger.info(f"⚠️ No fields to sync")
            return {
                "action": "skipped",
                "reason": "No field mappings configured",
                "sprawy_id": sprawy_id,
                "contact_id": contact_id
            }

        # Step 3: Get current Sprawy values to check if update needed
        logger.info(f"📗 Step 3: Checking current Sprawy values...")
        sprawy_fields = [m['sprawy_field'] for m in self.field_mappings]
        sprawy = self.bitrix.get_item(self.spa_sprawy, sprawy_id)

        # Compare and build update
        updates_needed = {}
        for field, new_value in field_values.items():
            current_value = sprawy.get(field, '')
            if current_value != new_value:
                updates_needed[field] = new_value
                logger.info(f"   📝 {field}: '{current_value}' → '{new_value}'")
            else:
                logger.info(f"   ✓ {field}: '{current_value}' (no change)")

        if not updates_needed:
            logger.info(f"✅ All fields already in sync - no update needed")
            return {
                "action": "already_synced",
                "sprawy_id": sprawy_id,
                "contact_id": contact_id,
                "fields": field_values
            }

        # Step 4: Update Sprawy
        logger.info(f"📗 Step 4: Updating Sprawy ID={sprawy_id}...")
        self.bitrix.update_item(
            entity_type_id=self.spa_sprawy,
            item_id=sprawy_id,
            fields=updates_needed
        )

        logger.info(f"✅ Sprawy {sprawy_id} updated with {len(updates_needed)} field(s)")

        return {
            "action": "synced",
            "sprawy_id": sprawy_id,
            "contact_id": contact_id,
            "updated_fields": updates_needed
        }

    def sync_contact_to_all_sprawy(
        self,
        contact_id: int
    ) -> Dict[str, Any]:
        """
        Sync field values from Contact to ALL linked Sprawy.

        Called when Contact is updated (ONCRMCONTACTUPDATE).

        Args:
            contact_id: Contact ID

        Returns:
            Sync result with details
        """
        logger.info("=" * 60)
        logger.info(f"🔄 SYNC CONTACT FIELDS to all Sprawy")
        logger.info(f"   Contact ID: {contact_id}")
        logger.info("=" * 60)

        # Step 1: Get Contact data for field values and title
        logger.info(f"👤 Step 1: Getting Contact data...")
        try:
            contact = self.bitrix.get_contact(contact_id)

            # Build field values from mappings
            field_values = {}
            for mapping in self.field_mappings:
                sprawy_field = mapping['sprawy_field']
                name = mapping['name']

                if 'contact_fields' in mapping:
                    fields = mapping['contact_fields']
                    format_str = mapping.get('format', ' '.join(['{' + str(i) + '}' for i in range(len(fields))]))
                    values = [contact.get(f, '') or '' for f in fields]
                    value = format_str.format(*values).strip()
                    logger.info(f"   📋 {name}: {fields} → '{value}'")
                else:
                    contact_field = mapping['contact_field']
                    value = contact.get(contact_field, '') or ''
                    logger.info(f"   📋 {name}: '{value}'")

                field_values[sprawy_field] = value

        except Exception as e:
            logger.error(f"❌ Failed to get Contact {contact_id}: {e}")
            return {
                "action": "error",
                "reason": f"Failed to get Contact: {e}",
                "contact_id": contact_id
            }

        if not field_values and not self.title_config.get('enabled'):
            logger.info(f"⚠️ No fields to sync")
            return {
                "action": "skipped",
                "reason": "No field mappings configured",
                "contact_id": contact_id
            }

        # Step 2: Find all Sprawy linked to this contact
        logger.info(f"📗 Step 2: Finding all Sprawy for contact {contact_id}...")
        sprawy_fields = [m['sprawy_field'] for m in self.field_mappings]
        sprawy_list = self.bitrix.list_items(
            entity_type_id=self.spa_sprawy,
            filter={'contactId': contact_id},
            select=['id', 'title'] + sprawy_fields
        )

        if not sprawy_list:
            logger.info(f"⚠️ No Sprawy found for contact {contact_id}")
            return {
                "action": "skipped",
                "reason": f"No Sprawy for contact {contact_id}",
                "contact_id": contact_id,
                "field_values": field_values
            }

        logger.info(f"   Found {len(sprawy_list)} Sprawy")

        # Step 3: Update each Sprawy
        logger.info(f"📗 Step 3: Updating Sprawy...")
        updated = []
        skipped = []

        for sprawy in sprawy_list:
            sprawy_id = sprawy['id']
            sprawy_title = sprawy.get('title', 'N/A')

            logger.info(f"   📗 Sprawy ID={sprawy_id}: {sprawy_title}")

            # Compare and build update for fields
            updates_needed = {}
            for field, new_value in field_values.items():
                current_value = sprawy.get(field, '')
                if current_value != new_value:
                    updates_needed[field] = new_value
                    logger.info(f"      📝 {field}: '{current_value}' → '{new_value}'")

            # Generate and check title
            new_title = self._generate_title(contact, sprawy_id)
            if new_title and sprawy_title != new_title:
                updates_needed['title'] = new_title
                logger.info(f"      🏷️ title: '{sprawy_title}' → '{new_title}'")

            if not updates_needed:
                logger.info(f"      ✓ Already in sync")
                skipped.append({
                    "sprawy_id": sprawy_id,
                    "title": sprawy_title,
                    "action": "already_synced"
                })
                continue

            # Update
            self.bitrix.update_item(
                entity_type_id=self.spa_sprawy,
                item_id=sprawy_id,
                fields=updates_needed
            )

            updated.append({
                "sprawy_id": sprawy_id,
                "title": sprawy_title,
                "action": "synced",
                "updated_fields": updates_needed
            })

        logger.info(f"")
        logger.info(f"=" * 60)
        logger.info(f"✅ CONTACT FIELDS SYNC COMPLETED")
        logger.info(f"   Contact: {contact_id}")
        logger.info(f"   Sprawy total: {len(sprawy_list)}")
        logger.info(f"   Updated: {len(updated)}")
        logger.info(f"   Already synced: {len(skipped)}")
        logger.info(f"=" * 60)

        return {
            "action": "sync_contact_fields",
            "contact_id": contact_id,
            "field_values": field_values,
            "sprawy_total": len(sprawy_list),
            "updated": updated,
            "skipped": skipped
        }

