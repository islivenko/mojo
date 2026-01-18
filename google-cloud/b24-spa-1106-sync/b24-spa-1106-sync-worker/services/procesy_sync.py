"""
Procesy Legalizacyjne Sync: Sprawy (1106) ↔ Procesy Legalizacyjne (1110)

Synchronizes the "Aktualne procesy legalizacyjne" field in Sprawy (SPA 1106)
with ACTIVE Procesy legalizacyjne items (SPA 1110) linked via the same contact.

Active = stageId NOT in SUCCESS/FAIL/FAILURE/LOSE stages

Flow:
1. On create/update Procesy (1110):
   - If ACTIVE → add ID to Sprawy.ufCrm38_1768738413
   - If NOT ACTIVE (SUCCESS/FAIL) → remove from Sprawy

2. On delete Procesy:
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
    Example: DT1110_58:SUCCESS, DT1110_58:NEW

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


class ProcesySyncService:
    """Service for syncing Sprawy ↔ Procesy Legalizacyjne relationships."""

    def __init__(
        self,
        bitrix: BitrixAPI,
        spa_sprawy: int = 1106,
        spa_procesy: int = 1110,
        field_procesy_link: str = "ufCrm38_1768738413"
    ):
        """
        Initialize procesy legalizacyjne sync service.

        Args:
            bitrix: Bitrix24 API client
            spa_sprawy: Entity type ID for Sprawy SPA (1106)
            spa_procesy: Entity type ID for Procesy legalizacyjne SPA (1110)
            field_procesy_link: Field in Sprawy that links to Procesy legalizacyjne
        """
        self.bitrix = bitrix
        self.spa_sprawy = spa_sprawy
        self.spa_procesy = spa_procesy
        self.field_procesy_link = field_procesy_link

        logger.info(f"🔧 ProcesySyncService initialized:")
        logger.info(f"   📗 Sprawy SPA: {spa_sprawy}")
        logger.info(f"   📋 Procesy SPA: {spa_procesy}")
        logger.info(f"   🔗 Link field: {field_procesy_link}")

    def sync_procesy_to_sprawy(
        self,
        procesy_id: int,
        contact_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Sync Procesy legalizacyjne to Sprawy.

        When a Procesy legalizacyjne is created/updated:
        1. Get its data (contactId, stageId)
        2. Check if ACTIVE (stageId not SUCCESS/FAIL)
        3. If active: add to Sprawy link field
        4. If not active: remove from Sprawy link field

        Args:
            procesy_id: Procesy legalizacyjne element ID
            contact_id: Contact ID (optional, will fetch if not provided)

        Returns:
            Sync result with details
        """
        logger.info("=" * 50)
        logger.info(f"🔄 SYNC: Procesy legalizacyjne ID={procesy_id} → Sprawy")
        logger.info("=" * 50)

        # Step 1: Get Procesy legalizacyjne data (always fetch to get stageId)
        logger.info(f"📋 Step 1: Fetching Procesy legalizacyjne ID={procesy_id}...")
        procesy = self.bitrix.get_item(self.spa_procesy, procesy_id)

        contact_id = contact_id or procesy.get('contactId')
        stage_id = procesy.get('stageId', '')
        title = procesy.get('title', 'N/A')
        is_active = is_active_stage(stage_id)

        logger.info(f"   📋 Title: {title}")
        logger.info(f"   👤 Contact ID: {contact_id}")
        logger.info(f"   📊 Stage: {stage_id}")
        logger.info(f"   {'✅ ACTIVE' if is_active else '❌ NOT ACTIVE (final stage)'}")

        if not contact_id:
            logger.warning(f"⚠️ Procesy legalizacyjne {procesy_id} has no contactId - skipping")
            return {
                "action": "skipped",
                "reason": "No contactId in Procesy legalizacyjne",
                "procesy_id": procesy_id
            }

        # If not active, remove from Sprawy instead of adding
        if not is_active:
            logger.info(f"🗑️ Removing inactive Procesy {procesy_id} from Sprawy...")
            return self.remove_procesy_from_sprawy(procesy_id, contact_id)

        # Step 2: Find Sprawy for this contact
        logger.info(f"📗 Step 2: Finding Sprawy for contact {contact_id}...")
        sprawy_list = self.bitrix.list_items(
            entity_type_id=self.spa_sprawy,
            filter={'contactId': contact_id},
            select=['id', 'title', self.field_procesy_link]
        )

        if not sprawy_list:
            logger.info(f"⚠️ No Sprawy found for contact {contact_id}")
            return {
                "action": "skipped",
                "reason": f"No Sprawy for contact {contact_id}",
                "procesy_id": procesy_id,
                "contact_id": contact_id
            }

        logger.info(f"   Found {len(sprawy_list)} Sprawy")

        # Step 3: Update each Sprawy (usually just one)
        logger.info(f"📗 Step 3: Adding link to Sprawy...")
        updated = []
        for sprawy in sprawy_list:
            sprawy_id = sprawy['id']
            sprawy_title = sprawy.get('title', 'N/A')
            current_links = sprawy.get(self.field_procesy_link, []) or []

            # Ensure it's a list of strings
            current_links = [str(x) for x in current_links]
            procesy_id_str = str(procesy_id)

            logger.info(f"   📗 Sprawy ID={sprawy_id}: {sprawy_title}")
            logger.info(f"      Current links: {current_links}")

            # Check if already linked
            if procesy_id_str in current_links:
                logger.info(f"      ✓ Already linked - no action needed")
                updated.append({
                    "sprawy_id": sprawy_id,
                    "action": "already_linked"
                })
                continue

            # Add the new link
            new_links = current_links + [procesy_id_str]
            logger.info(f"      ➕ Adding link: {current_links} → {new_links}")

            self.bitrix.update_item(
                entity_type_id=self.spa_sprawy,
                item_id=sprawy_id,
                fields={self.field_procesy_link: new_links}
            )

            updated.append({
                "sprawy_id": sprawy_id,
                "action": "linked",
                "previous_links": current_links,
                "new_links": new_links
            })

        logger.info(f"✅ Sync completed: {len(updated)} Sprawy processed")
        return {
            "action": "synced",
            "procesy_id": procesy_id,
            "contact_id": contact_id,
            "updated_sprawy": updated
        }

    def remove_procesy_from_sprawy(
        self,
        procesy_id: int,
        contact_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Remove Procesy legalizacyjne link from Sprawy.

        When a Procesy legalizacyjne is deleted or moved to final stage:
        1. Find all Sprawy that have this ID in their links
        2. Remove the ID from the link field

        Args:
            procesy_id: Procesy legalizacyjne element ID
            contact_id: Contact ID (optional, for faster lookup)

        Returns:
            Sync result with details
        """
        logger.info("=" * 50)
        logger.info(f"🗑️ REMOVE: Procesy legalizacyjne ID={procesy_id} from Sprawy")
        logger.info("=" * 50)

        procesy_id_str = str(procesy_id)

        # Find Sprawy to update
        if contact_id:
            logger.info(f"📗 Finding Sprawy by contact {contact_id}...")
            sprawy_list = self.bitrix.list_items(
                entity_type_id=self.spa_sprawy,
                filter={'contactId': contact_id},
                select=['id', 'title', self.field_procesy_link]
            )
        else:
            logger.info(f"📗 Finding all Sprawy (no contact filter)...")
            sprawy_list = self.bitrix.list_items(
                entity_type_id=self.spa_sprawy,
                select=['id', 'title', self.field_procesy_link]
            )

        logger.info(f"   Found {len(sprawy_list)} Sprawy to check")

        updated = []
        for sprawy in sprawy_list:
            sprawy_id = sprawy['id']
            sprawy_title = sprawy.get('title', 'N/A')
            current_links = sprawy.get(self.field_procesy_link, []) or []
            current_links = [str(x) for x in current_links]

            if procesy_id_str not in current_links:
                logger.debug(f"   📗 Sprawy {sprawy_id}: link not present - skipping")
                continue

            # Remove the link
            new_links = [x for x in current_links if x != procesy_id_str]

            logger.info(f"   📗 Sprawy ID={sprawy_id}: {sprawy_title}")
            logger.info(f"      ➖ Removing link: {current_links} → {new_links}")

            self.bitrix.update_item(
                entity_type_id=self.spa_sprawy,
                item_id=sprawy_id,
                fields={self.field_procesy_link: new_links}
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
            "procesy_id": procesy_id,
            "updated_sprawy": updated
        }

    def sync_all_for_contact(self, contact_id: int) -> Dict[str, Any]:
        """
        Full sync: Find all ACTIVE Procesy legalizacyjne for a contact and sync to Sprawy.

        Only active items (stageId not SUCCESS/FAIL) are included in the link field.
        This REPLACES current links with only active items (removes inactive).

        Args:
            contact_id: Contact ID

        Returns:
            Sync result with details
        """
        logger.info("=" * 60)
        logger.info(f"🔄 FULL PROCESY SYNC for Contact ID={contact_id}")
        logger.info("=" * 60)

        # Step 1: Get all Procesy legalizacyjne for this contact
        logger.info(f"📋 Step 1: Fetching all Procesy legalizacyjne for contact {contact_id}...")
        procesy_list = self.bitrix.list_items(
            entity_type_id=self.spa_procesy,
            filter={'contactId': contact_id},
            select=['id', 'title', 'stageId']
        )

        if not procesy_list:
            logger.info(f"⚠️ No Procesy legalizacyjne found for contact {contact_id}")
            return {
                "action": "sync_all",
                "contact_id": contact_id,
                "procesy_total": 0,
                "procesy_active": 0,
                "result": "No Procesy legalizacyjne to sync"
            }

        # Step 2: Filter only ACTIVE procesy
        logger.info(f"📊 Step 2: Filtering active items...")
        all_ids = []
        active_procesy = []
        inactive_procesy = []

        for p in procesy_list:
            p_id = str(p['id'])
            p_title = p.get('title', 'N/A')
            p_stage = p.get('stageId', '')
            p_active = is_active_stage(p_stage)

            all_ids.append(p_id)

            if p_active:
                active_procesy.append(p)
                logger.info(f"   ✅ ID={p_id}: {p_title} [{p_stage}]")
            else:
                inactive_procesy.append(p)
                logger.info(f"   ❌ ID={p_id}: {p_title} [{p_stage}] - INACTIVE")

        active_ids = [str(p['id']) for p in active_procesy]
        inactive_ids = [str(p['id']) for p in inactive_procesy]

        logger.info(f"")
        logger.info(f"📈 Summary: {len(all_ids)} total, {len(active_ids)} active, {len(inactive_ids)} inactive")
        logger.info(f"   Active IDs: {active_ids}")
        logger.info(f"   Inactive IDs: {inactive_ids}")

        # Step 3: Find Sprawy for this contact
        logger.info(f"")
        logger.info(f"📗 Step 3: Finding Sprawy for contact {contact_id}...")
        sprawy_list = self.bitrix.list_items(
            entity_type_id=self.spa_sprawy,
            filter={'contactId': contact_id},
            select=['id', 'title', self.field_procesy_link]
        )

        if not sprawy_list:
            logger.info(f"⚠️ No Sprawy found for contact {contact_id}")
            return {
                "action": "sync_all",
                "contact_id": contact_id,
                "procesy_total": len(all_ids),
                "procesy_active": len(active_ids),
                "result": "No Sprawy to update"
            }

        logger.info(f"   Found {len(sprawy_list)} Sprawy")

        # Step 4: Update each Sprawy with ONLY ACTIVE Procesy IDs
        logger.info(f"")
        logger.info(f"📗 Step 4: Updating Sprawy with active links only...")
        updated = []
        for sprawy in sprawy_list:
            sprawy_id = sprawy['id']
            sprawy_title = sprawy.get('title', 'N/A')
            current_links = sprawy.get(self.field_procesy_link, []) or []
            current_links = [str(x) for x in current_links]

            # Replace with only active IDs (not merge!)
            new_links = sorted(active_ids)

            logger.info(f"   📗 Sprawy ID={sprawy_id}: {sprawy_title}")
            logger.info(f"      Current: {current_links}")
            logger.info(f"      Target:  {new_links}")

            if set(current_links) == set(new_links):
                logger.info(f"      ✓ Already in sync - no action needed")
                updated.append({
                    "sprawy_id": sprawy_id,
                    "action": "already_synced"
                })
                continue

            # Calculate diff for logging
            added = set(new_links) - set(current_links)
            removed = set(current_links) - set(new_links)
            if added:
                logger.info(f"      ➕ Adding: {list(added)}")
            if removed:
                logger.info(f"      ➖ Removing: {list(removed)}")

            self.bitrix.update_item(
                entity_type_id=self.spa_sprawy,
                item_id=sprawy_id,
                fields={self.field_procesy_link: new_links}
            )

            updated.append({
                "sprawy_id": sprawy_id,
                "action": "synced",
                "previous_links": current_links,
                "new_links": new_links,
                "added": list(added),
                "removed": list(removed)
            })

        logger.info(f"")
        logger.info(f"=" * 60)
        logger.info(f"✅ FULL PROCESY SYNC COMPLETED")
        logger.info(f"   Contact: {contact_id}")
        logger.info(f"   Procesy: {len(active_ids)}/{len(all_ids)} active")
        logger.info(f"   Sprawy updated: {len([u for u in updated if u['action'] == 'synced'])}")
        logger.info(f"=" * 60)

        return {
            "action": "sync_all",
            "contact_id": contact_id,
            "procesy_total": len(all_ids),
            "procesy_active": len(active_ids),
            "active_ids": active_ids,
            "inactive_ids": inactive_ids,
            "updated_sprawy": updated
        }
