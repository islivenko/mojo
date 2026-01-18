"""
Podstawy Pobytu Sync: Sprawy (1106) ↔ Podstawy Pobytu (1042)

Synchronizes the "Aktualne Podstawy pobytu" field in Sprawy (SPA 1106)
with ACTIVE Podstawy pobytu items (SPA 1042) linked via the same contact.

Active = stageId NOT in SUCCESS/FAIL/FAILURE/LOSE stages

Flow:
1. On create/update Podstawy (1042):
   - If ACTIVE → add ID to Sprawy.ufCrm38_1768737959
   - If NOT ACTIVE (SUCCESS/FAIL) → remove from Sprawy

2. On delete Podstawy:
   - Remove ID from Sprawy
"""

import logging
from typing import Optional, Dict, List, Any

from .bitrix_api import BitrixAPI

logger = logging.getLogger('b24-sync')

# Final stages - items in these stages are NOT active
FINAL_STAGES = {'SUCCESS', 'FAIL', 'FAILURE', 'LOSE', 'APOLOGY'}


def is_active_stage(stage_id: str) -> bool:
    """
    Check if stageId represents an active (non-final) stage.

    Bitrix24 stage format: DT{entityTypeId}_{categoryId}:{STAGE_NAME}
    Example: DT1042_20:SUCCESS, DT1042_20:NEW

    Args:
        stage_id: Bitrix24 stageId

    Returns:
        True if stage is active (not final)
    """
    if not stage_id:
        return True  # Assume active if no stage

    # Extract stage name after the last ':'
    parts = stage_id.split(':')
    if len(parts) < 2:
        return True

    stage_name = parts[-1].upper()
    is_active = stage_name not in FINAL_STAGES

    logger.debug(f"   Stage check: {stage_id} → {stage_name} → active={is_active}")
    return is_active


class PodstawyPobytSyncService:
    """Service for syncing Sprawy ↔ Podstawy Pobytu relationships."""

    def __init__(
        self,
        bitrix: BitrixAPI,
        spa_sprawy: int = 1106,
        spa_podstawy: int = 1042,
        field_podstawy_link: str = "ufCrm38_1768737959",
        field_podstawy_dates: str = "ufCrm38_1768738011252",
        field_podstawy_data_do_kiedy: str = "ufCrm10_1763581700754"
    ):
        """
        Initialize podstawy pobytu sync service.

        Args:
            bitrix: Bitrix24 API client
            spa_sprawy: Entity type ID for Sprawy SPA (1106)
            spa_podstawy: Entity type ID for Podstawy pobytu SPA (1042)
            field_podstawy_link: Field in Sprawy that links to Podstawy pobytu
            field_podstawy_dates: Field in Sprawy for "Data ważności podstawy pobytu" (multiple dates)
            field_podstawy_data_do_kiedy: Field in Podstawy for "Data do kiedy"
        """
        self.bitrix = bitrix
        self.spa_sprawy = spa_sprawy
        self.spa_podstawy = spa_podstawy
        self.field_podstawy_link = field_podstawy_link
        self.field_podstawy_dates = field_podstawy_dates
        self.field_podstawy_data_do_kiedy = field_podstawy_data_do_kiedy

        logger.info(f"🔧 PodstawyPobytSyncService initialized:")
        logger.info(f"   📗 Sprawy SPA: {spa_sprawy}")
        logger.info(f"   📘 Podstawy SPA: {spa_podstawy}")
        logger.info(f"   🔗 Link field: {field_podstawy_link}")
        logger.info(f"   📅 Dates field: {field_podstawy_dates}")
        logger.info(f"   📅 Data do kiedy field: {field_podstawy_data_do_kiedy}")

    def sync_podstawy_to_sprawy(
        self,
        podstawy_id: int,
        contact_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Sync Podstawy pobytu to Sprawy.

        When a Podstawy pobytu is created/updated:
        1. Get its data (contactId, stageId)
        2. Perform full sync for the contact (links + dates)

        This ensures that both links AND dates are always in sync.

        Args:
            podstawy_id: Podstawy pobytu element ID
            contact_id: Contact ID (optional, will fetch if not provided)

        Returns:
            Sync result with details
        """
        logger.info("=" * 50)
        logger.info(f"🔄 SYNC: Podstawy pobytu ID={podstawy_id} → Sprawy")
        logger.info("=" * 50)

        # Step 1: Get Podstawy pobytu data to extract contact_id
        logger.info(f"📘 Step 1: Fetching Podstawy pobytu ID={podstawy_id}...")
        podstawy = self.bitrix.get_item(self.spa_podstawy, podstawy_id)

        contact_id = contact_id or podstawy.get('contactId')
        stage_id = podstawy.get('stageId', '')
        title = podstawy.get('title', 'N/A')
        date = podstawy.get(self.field_podstawy_data_do_kiedy, 'N/A')

        logger.info(f"   📋 Title: {title}")
        logger.info(f"   👤 Contact ID: {contact_id}")
        logger.info(f"   📊 Stage: {stage_id}")
        logger.info(f"   📅 Data do kiedy: {date}")

        if not contact_id:
            logger.warning(f"⚠️ Podstawy pobytu {podstawy_id} has no contactId - skipping")
            return {
                "action": "skipped",
                "reason": "No contactId in Podstawy pobytu",
                "podstawy_id": podstawy_id
            }

        # Step 2: Perform full sync for this contact (updates both links and dates)
        logger.info(f"")
        logger.info(f"📗 Step 2: Performing full sync for contact {contact_id}...")
        logger.info(f"   This will sync ALL active Podstawy (links + dates)")

        result = self.sync_all_for_contact(contact_id)

        # Add info about the trigger
        result['trigger_podstawy_id'] = podstawy_id
        result['trigger_action'] = 'podstawy_updated'

        return result

    def remove_podstawy_from_sprawy(
        self,
        podstawy_id: int,
        contact_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Remove Podstawy pobytu link from Sprawy.

        When a Podstawy pobytu is deleted or moved to final stage:
        1. Find all Sprawy that have this ID in their links
        2. Remove the ID from the link field

        Args:
            podstawy_id: Podstawy pobytu element ID
            contact_id: Contact ID (optional, for faster lookup)

        Returns:
            Sync result with details
        """
        logger.info("=" * 50)
        logger.info(f"🗑️ REMOVE: Podstawy pobytu ID={podstawy_id} from Sprawy")
        logger.info("=" * 50)

        podstawy_id_str = str(podstawy_id)

        # Find Sprawy to update
        if contact_id:
            logger.info(f"📗 Finding Sprawy by contact {contact_id}...")
            sprawy_list = self.bitrix.list_items(
                entity_type_id=self.spa_sprawy,
                filter={'contactId': contact_id},
                select=['id', 'title', self.field_podstawy_link]
            )
        else:
            logger.info(f"📗 Finding all Sprawy (no contact filter)...")
            sprawy_list = self.bitrix.list_items(
                entity_type_id=self.spa_sprawy,
                select=['id', 'title', self.field_podstawy_link]
            )

        logger.info(f"   Found {len(sprawy_list)} Sprawy to check")

        updated = []
        for sprawy in sprawy_list:
            sprawy_id = sprawy['id']
            sprawy_title = sprawy.get('title', 'N/A')
            current_links = sprawy.get(self.field_podstawy_link, []) or []
            current_links = [str(x) for x in current_links]

            if podstawy_id_str not in current_links:
                logger.debug(f"   📗 Sprawy {sprawy_id}: link not present - skipping")
                continue

            # Remove the link
            new_links = [x for x in current_links if x != podstawy_id_str]

            logger.info(f"   📗 Sprawy ID={sprawy_id}: {sprawy_title}")
            logger.info(f"      ➖ Removing link: {current_links} → {new_links}")

            self.bitrix.update_item(
                entity_type_id=self.spa_sprawy,
                item_id=sprawy_id,
                fields={self.field_podstawy_link: new_links}
            )

            updated.append({
                "sprawy_id": sprawy_id,
                "action": "unlinked",
                "previous_links": current_links,
                "new_links": new_links
            })

        if updated:
            logger.info(f"✅ Removed from {len(updated)} Sprawy")
        else:
            logger.info(f"ℹ️ Link was not present in any Sprawy")

        return {
            "action": "removed",
            "podstawy_id": podstawy_id,
            "updated_sprawy": updated
        }

    def sync_all_for_contact(self, contact_id: int) -> Dict[str, Any]:
        """
        Full sync: Find all ACTIVE Podstawy pobytu for a contact and sync to Sprawy.

        Only active items (stageId not SUCCESS/FAIL) are included in the link field.
        This REPLACES current links with only active items (removes inactive).

        Args:
            contact_id: Contact ID

        Returns:
            Sync result with details
        """
        logger.info("=" * 60)
        logger.info(f"🔄 FULL SYNC for Contact ID={contact_id}")
        logger.info("=" * 60)

        # Step 1: Get all Podstawy pobytu for this contact
        logger.info(f"📘 Step 1: Fetching all Podstawy pobytu for contact {contact_id}...")
        podstawy_list = self.bitrix.list_items(
            entity_type_id=self.spa_podstawy,
            filter={'contactId': contact_id},
            select=['id', 'title', 'stageId', self.field_podstawy_data_do_kiedy]
        )

        if not podstawy_list:
            logger.info(f"⚠️ No Podstawy pobytu found for contact {contact_id}")
            return {
                "action": "sync_all",
                "contact_id": contact_id,
                "podstawy_total": 0,
                "podstawy_active": 0,
                "result": "No Podstawy pobytu to sync"
            }

        # Step 2: Filter only ACTIVE podstawy and collect dates
        logger.info(f"📊 Step 2: Filtering active items and collecting dates...")
        all_ids = []
        active_podstawy = []
        inactive_podstawy = []
        # Create mapping: ID -> Date for active Podstawy
        active_podstawy_map = {}  # {id: date}

        for p in podstawy_list:
            p_id = str(p['id'])
            p_title = p.get('title', 'N/A')
            p_stage = p.get('stageId', '')
            p_date = p.get(self.field_podstawy_data_do_kiedy, '')
            p_active = is_active_stage(p_stage)

            all_ids.append(p_id)

            if p_active:
                active_podstawy.append(p)
                active_podstawy_map[p_id] = p_date
                if p_date:
                    logger.info(f"   ✅ ID={p_id}: {p_title} [{p_stage}] → Data: {p_date}")
                else:
                    logger.info(f"   ✅ ID={p_id}: {p_title} [{p_stage}] → No date")
            else:
                inactive_podstawy.append(p)
                logger.info(f"   ❌ ID={p_id}: {p_title} [{p_stage}] - INACTIVE")

        active_ids = [str(p['id']) for p in active_podstawy]
        inactive_ids = [str(p['id']) for p in inactive_podstawy]

        logger.info(f"")
        logger.info(f"📈 Summary: {len(all_ids)} total, {len(active_ids)} active, {len(inactive_ids)} inactive")
        logger.info(f"   Active IDs: {active_ids}")
        logger.info(f"   Active Dates mapping: {active_podstawy_map}")
        logger.info(f"   Inactive IDs: {inactive_ids}")

        # Step 3: Find Sprawy for this contact
        logger.info(f"")
        logger.info(f"📗 Step 3: Finding Sprawy for contact {contact_id}...")
        sprawy_list = self.bitrix.list_items(
            entity_type_id=self.spa_sprawy,
            filter={'contactId': contact_id},
            select=['id', 'title', self.field_podstawy_link, self.field_podstawy_dates]
        )

        if not sprawy_list:
            logger.info(f"⚠️ No Sprawy found for contact {contact_id}")
            return {
                "action": "sync_all",
                "contact_id": contact_id,
                "podstawy_total": len(all_ids),
                "podstawy_active": len(active_ids),
                "result": "No Sprawy to update"
            }

        logger.info(f"   Found {len(sprawy_list)} Sprawy")

        # Step 4: Update each Sprawy with ONLY ACTIVE Podstawy IDs and dates
        logger.info(f"")
        logger.info(f"📗 Step 4: Updating Sprawy with active links and dates...")
        updated = []
        for sprawy in sprawy_list:
            sprawy_id = sprawy['id']
            sprawy_title = sprawy.get('title', 'N/A')
            current_links = sprawy.get(self.field_podstawy_link, []) or []
            current_links = [str(x) for x in current_links]
            current_dates = sprawy.get(self.field_podstawy_dates, []) or []

            # Replace with only active IDs and dates (not merge!)
            # Sort IDs first
            new_links = sorted(active_ids)
            # Build dates list in the same order as links
            new_dates = [active_podstawy_map.get(link_id, '') for link_id in new_links]
            # Remove empty dates
            new_dates = [d for d in new_dates if d]

            logger.info(f"   📗 Sprawy ID={sprawy_id}: {sprawy_title}")
            logger.info(f"      Current links: {current_links}")
            logger.info(f"      Target links:  {new_links}")
            logger.info(f"      Current dates: {current_dates}")
            logger.info(f"      Target dates:  {new_dates}")
            logger.info(f"      Dates order matches links: {len(new_links) == len(new_dates)}")

            # Check if both links and dates are in sync
            # Compare lists directly (order matters for both links and dates)
            links_in_sync = current_links == new_links
            dates_in_sync = current_dates == new_dates

            if links_in_sync and dates_in_sync:
                logger.info(f"      ✓ Already in sync - no action needed")
                updated.append({
                    "sprawy_id": sprawy_id,
                    "action": "already_synced"
                })
                continue

            # Calculate diff for logging
            fields_to_update = {}

            if not links_in_sync:
                added = set(new_links) - set(current_links)
                removed = set(current_links) - set(new_links)
                if added:
                    logger.info(f"      ➕ Adding links: {list(added)}")
                if removed:
                    logger.info(f"      ➖ Removing links: {list(removed)}")
                fields_to_update[self.field_podstawy_link] = new_links

            if not dates_in_sync:
                added_dates = set(new_dates) - set(current_dates)
                removed_dates = set(current_dates) - set(new_dates)
                if added_dates:
                    logger.info(f"      ➕ Adding dates: {list(added_dates)}")
                if removed_dates:
                    logger.info(f"      ➖ Removing dates: {list(removed_dates)}")
                fields_to_update[self.field_podstawy_dates] = new_dates

            # Update Sprawy
            self.bitrix.update_item(
                entity_type_id=self.spa_sprawy,
                item_id=sprawy_id,
                fields=fields_to_update
            )

            updated.append({
                "sprawy_id": sprawy_id,
                "action": "synced",
                "previous_links": current_links,
                "new_links": new_links,
                "previous_dates": current_dates,
                "new_dates": new_dates,
                "links_updated": not links_in_sync,
                "dates_updated": not dates_in_sync
            })

        logger.info(f"")
        logger.info(f"=" * 60)
        logger.info(f"✅ FULL SYNC COMPLETED")
        logger.info(f"   Contact: {contact_id}")
        logger.info(f"   Podstawy: {len(active_ids)}/{len(all_ids)} active")
        logger.info(f"   Sprawy updated: {len([u for u in updated if u['action'] == 'synced'])}")
        logger.info(f"=" * 60)

        return {
            "action": "sync_all",
            "contact_id": contact_id,
            "podstawy_total": len(all_ids),
            "podstawy_active": len(active_ids),
            "active_ids": active_ids,
            "inactive_ids": inactive_ids,
            "updated_sprawy": updated
        }
