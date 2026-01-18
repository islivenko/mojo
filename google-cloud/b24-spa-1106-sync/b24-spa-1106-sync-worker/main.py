"""
B24 SPA 1106 Sync Worker
Pub/Sub triggered function for Sprawy cudzoziemców (1106) synchronization.

Handles events from multiple SPA types:
- 1106 (Sprawy cudzoziemców): Full sync for contact (all linked SPAs + Contact fields)
- 1042 (Podstawy pobytu): Sync specific item to Sprawy
- 1046 (Uprawnienia do pracy): Sync specific item to Sprawy
- 1110 (Procesy legalizacyjne): Sync specific item to Sprawy

Contact events:
- ONCRMCONTACTADD/UPDATE: Sync Contact fields (passport) to all linked Sprawy
- ONCRMCONTACTDELETE: (no action needed)

Daily sync:
- event=daily_sync: Triggered by Cloud Scheduler for periodic full sync

Project: mojo_agency
"""

import os
import sys
import json
import logging
import base64
import time
from datetime import datetime
import functions_framework
from cloudevents.http import CloudEvent

from services.bitrix_api import BitrixAPI
from services.pobyt_sync import PodstawyPobytSyncService
from services.praca_sync import PracaSyncService
from services.procesy_sync import ProcesySyncService
from services.contact_sync import ContactFieldsSyncService


class StructuredLogHandler(logging.Handler):
    """Custom handler that outputs structured JSON logs for Cloud Run"""
    def emit(self, record):
        log_entry = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "logger": record.name,
        }
        print(json.dumps(log_entry, ensure_ascii=False, default=str), flush=True)


# Configure structured logging
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers = []  # Clear default handlers
root_logger.addHandler(StructuredLogHandler())

logger = logging.getLogger('b24-spa-1106-sync-worker')


def log(msg):
    """Log message to Cloud Logging."""
    logger.info(msg)


# Configuration
PROJECT_ID = os.getenv("PROJECT_ID")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET", "b24-access-token")
B24_DOMAIN = os.getenv("B24_DOMAIN", "mojo.bitrix24.pl")

# SPA Entity Type IDs
SPA_SPRAWY = int(os.getenv("SPA_SPRAWY_ID", "1106"))
SPA_PODSTAWY_POBYTU = int(os.getenv("SPA_PODSTAWY_POBYTU_ID", "1042"))
SPA_PRACA = int(os.getenv("SPA_PRACA_ID", "1046"))
SPA_PROCESY = int(os.getenv("SPA_PROCESY_ID", "1110"))

# Fields for linking SPAs in Sprawy
FIELD_SPRAWY_PODSTAWY = os.getenv("FIELD_SPRAWY_PODSTAWY", "ufCrm38_1768737959")
FIELD_SPRAWY_PRACA = os.getenv("FIELD_SPRAWY_PRACA", "ufCrm38_1768738112")
FIELD_SPRAWY_PROCESY = os.getenv("FIELD_SPRAWY_PROCESY", "ufCrm38_1768738413")

# Additional fields for Podstawy pobytu sync
FIELD_SPRAWY_PODSTAWY_DATES = os.getenv("FIELD_SPRAWY_PODSTAWY_DATES", "ufCrm38_1768738011252")
FIELD_PODSTAWY_DATA_DO_KIEDY = os.getenv("FIELD_PODSTAWY_DATA_DO_KIEDY", "ufCrm10_1763581700754")


def get_services():
    """Initialize Bitrix API and Sync Services."""
    bitrix = BitrixAPI(
        domain=B24_DOMAIN,
        project_id=PROJECT_ID,
        access_token_secret=ACCESS_TOKEN_SECRET
    )

    # Podstawy pobytu sync service
    podstawy_sync = PodstawyPobytSyncService(
        bitrix=bitrix,
        spa_sprawy=SPA_SPRAWY,
        spa_podstawy=SPA_PODSTAWY_POBYTU,
        field_podstawy_link=FIELD_SPRAWY_PODSTAWY,
        field_podstawy_dates=FIELD_SPRAWY_PODSTAWY_DATES,
        field_podstawy_data_do_kiedy=FIELD_PODSTAWY_DATA_DO_KIEDY
    )

    # Praca sync service
    praca_sync = PracaSyncService(
        bitrix=bitrix,
        spa_sprawy=SPA_SPRAWY,
        spa_praca=SPA_PRACA,
        field_praca_link=FIELD_SPRAWY_PRACA
    )

    # Procesy legalizacyjne sync service
    procesy_sync = ProcesySyncService(
        bitrix=bitrix,
        spa_sprawy=SPA_SPRAWY,
        spa_procesy=SPA_PROCESY,
        field_procesy_link=FIELD_SPRAWY_PROCESY
    )

    # Contact fields sync service (passport fields)
    contact_sync = ContactFieldsSyncService(
        bitrix=bitrix,
        spa_sprawy=SPA_SPRAWY
    )

    return bitrix, podstawy_sync, praca_sync, procesy_sync, contact_sync


@functions_framework.cloud_event
def main(cloud_event: CloudEvent):
    """
    Pub/Sub triggered Cloud Function.

    Processes sync events from b24-spa-1106-http webhook handler.

    Message format:
    {
        "event": "podstawy_created|podstawy_updated|podstawy_deleted|sync_all",
        "id": "123",
        "contact_id": "456",
        "entity_type_id": "1106|1042|1046|1110",
        "bitrix_event": "ONCRMDYNAMICITEMUPDATE|ADD|DELETE"
    }

    Routing logic by entity_type_id:
    - 1106 (Sprawy): Full sync for contact (Podstawy + Praca + Contact fields)
    - 1042 (Podstawy pobytu): Sync specific item to Sprawy
    - 1046 (Uprawnienia do pracy): Sync specific item to Sprawy
    - 1110 (Procesy legalizacyjne): Log only (not implemented yet)
    """
    start_time = time.time()

    log("=" * 70)
    log("📨 B24 SPA 1106 SYNC WORKER TRIGGERED")
    log("=" * 70)

    # Decode Pub/Sub message
    try:
        message_data = base64.b64decode(cloud_event.data["message"]["data"]).decode()
        message = json.loads(message_data)
        log(f"📋 Message parsed successfully")
        log(f"   Event: {message.get('event', 'N/A')}")
        log(f"   ID: {message.get('id', 'N/A')}")
        log(f"   Contact ID: {message.get('contact_id', 'N/A')}")
        log(f"   Entity Type: {message.get('entity_type_id', 'N/A')}")
        log(f"   Request ID: {message.get('request_id', 'N/A')}")
    except Exception as e:
        log(f"❌ Failed to parse Pub/Sub message: {type(e).__name__}: {e}")
        return  # Don't retry on parse errors

    event = message.get('event', 'sprawy_updated')
    item_id = message.get('id')
    contact_id = message.get('contact_id')
    entity_type_id = message.get('entity_type_id')
    is_contact_event = message.get('is_contact_event', False)
    bitrix_event = message.get('bitrix_event', '')
    request_id = message.get('request_id', 'unknown')

    # Convert IDs to int if present
    try:
        item_id = int(item_id) if item_id else None
        contact_id = int(contact_id) if contact_id else None
        # entity_type_id can be "CONTACT" for contact events
        if entity_type_id and entity_type_id != "CONTACT":
            entity_type_id = int(entity_type_id)
    except ValueError as e:
        log(f"❌ Invalid ID format: {type(e).__name__}: {e}")
        return

    log(f"")
    log(f"🔍 [{request_id}] Processing event:")

    # Validate
    if not item_id and event != 'sync_all':
        log(f"⚠️ [{request_id}] Missing item_id, skipping")
        return

    if event == 'sync_all' and not contact_id:
        log(f"⚠️ [{request_id}] sync_all requires contact_id, skipping")
        return

    # Initialize services
    init_start = time.time()
    try:
        log(f"🔧 [{request_id}] Initializing services...")
        log(f"   Project: {PROJECT_ID}")
        log(f"   Domain: {B24_DOMAIN}")
        log(f"   SPA Sprawy: {SPA_SPRAWY}")
        log(f"   SPA Podstawy: {SPA_PODSTAWY_POBYTU}")
        log(f"   SPA Praca: {SPA_PRACA}")
        log(f"   SPA Procesy: {SPA_PROCESY}")

        bitrix, podstawy_sync, praca_sync, procesy_sync, contact_sync = get_services()
        init_time = time.time() - init_start
        log(f"✅ [{request_id}] Services initialized in {init_time:.2f}s")
    except Exception as e:
        log(f"❌ [{request_id}] Failed to initialize services: {type(e).__name__}: {e}")
        raise  # Retry on service init failure

    # Process event based on entity_type_id or contact event
    sync_start = time.time()
    try:
        # Handle Contact events first
        if is_contact_event or entity_type_id == "CONTACT":
            log(f"👤 [{request_id}] Contact event detected")
            log(f"   Contact ID: {contact_id}")
            log(f"   Event: {event}")

            if not contact_id:
                log(f"⚠️ [{request_id}] Contact event missing contact_id, skipping")
                return

            if event == 'contact_deleted':
                log(f"🗑️ [{request_id}] Contact deleted - no sync needed")
                result = {"action": "skipped", "reason": "Contact deleted", "contact_id": contact_id}
            else:
                # Contact created or updated - sync passport fields to all linked Sprawy
                log(f"🔄 [{request_id}] Syncing Contact passport fields to all Sprawy...")
                log(f"   Fields: Numer paszportu, Data ważności")
                result = contact_sync.sync_contact_to_all_sprawy(contact_id)
                log(f"✅ [{request_id}] Contact sync completed")
                log(f"   Sprawy updated: {result.get('updated', [])}")

        elif entity_type_id == SPA_SPRAWY:
            # Event from Sprawy (1106) - do full sync for all linked SPAs + Contact fields
            if event == 'daily_sync':
                log(f"📅 [{request_id}] DAILY SYNC: Sprawy ID={item_id}")
            else:
                log(f"📋 [{request_id}] Event from SPA 1106 (Sprawy cudzoziemców)")
                log(f"   Sprawy ID: {item_id}")

            # Get contact_id from Sprawy if not provided
            if not contact_id:
                log(f"🔍 [{request_id}] Fetching contact_id from Sprawy {item_id}...")
                sprawy = bitrix.get_item(SPA_SPRAWY, item_id)
                contact_id = sprawy.get('contactId')
                log(f"✅ [{request_id}] Found contact_id: {contact_id}")

            if contact_id:
                # Sync Podstawy pobytu, Praca, Procesy AND Contact fields for this contact
                log(f"")
                log(f"🔄 [{request_id}] Starting FULL SYNC for contact {contact_id}")
                log(f"   Syncing: Podstawy pobytu + Uprawnienia do pracy + Procesy legalizacyjne + Passport fields")

                # Sync SPA links
                log(f"")
                log(f"📗 [{request_id}] Step 1/4: Syncing Podstawy pobytu (SPA 1042)...")
                result_podstawy = podstawy_sync.sync_all_for_contact(contact_id)

                log(f"")
                log(f"💼 [{request_id}] Step 2/4: Syncing Uprawnienia do pracy (SPA 1046)...")
                result_praca = praca_sync.sync_all_praca_for_contact(contact_id)

                log(f"")
                log(f"📋 [{request_id}] Step 3/4: Syncing Procesy legalizacyjne (SPA 1110)...")
                result_procesy = procesy_sync.sync_all_for_contact(contact_id)

                # Sync Contact fields to this specific Sprawy
                log(f"")
                log(f"👤 [{request_id}] Step 4/4: Syncing Contact passport fields to Sprawy {item_id}...")
                result_contact = contact_sync.sync_fields_to_sprawy(item_id, contact_id)

                result = {
                    "action": "full_sync",
                    "contact_id": contact_id,
                    "sprawy_id": item_id,
                    "podstawy_sync": result_podstawy,
                    "praca_sync": result_praca,
                    "procesy_sync": result_procesy,
                    "contact_sync": result_contact
                }

                log(f"")
                log(f"✅ [{request_id}] FULL SYNC COMPLETED")
                log(f"   Podstawy: {result_podstawy.get('action', 'N/A')}")
                log(f"   Praca: {result_praca.get('action', 'N/A')}")
                log(f"   Procesy: {result_procesy.get('action', 'N/A')}")
                log(f"   Contact: {result_contact.get('action', 'N/A')}")
            else:
                log(f"⚠️ [{request_id}] Sprawy {item_id} has no contactId, skipping")
                return

        elif entity_type_id == SPA_PODSTAWY_POBYTU:
            # Event from Podstawy pobytu (1042) - sync specific item
            log(f"📗 [{request_id}] Event from SPA 1042 (Podstawy pobytu)")
            log(f"   Item ID: {item_id}")
            log(f"   Contact ID: {contact_id}")
            log(f"   Event: {event}")

            if event in ('podstawy_created', 'podstawy_updated'):
                log(f"🔄 [{request_id}] Syncing Podstawy item {item_id} to Sprawy...")
                result = podstawy_sync.sync_podstawy_to_sprawy(item_id, contact_id)
                log(f"✅ [{request_id}] Podstawy sync completed: {result.get('action')}")
            elif event == 'podstawy_deleted':
                log(f"🗑️ [{request_id}] Removing Podstawy item {item_id} from Sprawy...")
                result = podstawy_sync.remove_podstawy_from_sprawy(item_id, contact_id)
                log(f"✅ [{request_id}] Podstawy removed: {result.get('action')}")
            else:
                # Default to update for unknown events
                log(f"🔄 [{request_id}] Unknown event, defaulting to update...")
                result = podstawy_sync.sync_podstawy_to_sprawy(item_id, contact_id)

        elif entity_type_id == SPA_PRACA:
            # Event from Uprawnienia do pracy (1046) - sync specific item
            log(f"💼 [{request_id}] Event from SPA 1046 (Uprawnienia do pracy)")
            log(f"   Item ID: {item_id}")
            log(f"   Contact ID: {contact_id}")
            log(f"   Bitrix Event: {bitrix_event}")

            if 'DELETE' in (bitrix_event or '').upper():
                log(f"🗑️ [{request_id}] Removing Praca item {item_id} from Sprawy...")
                result = praca_sync.remove_praca_from_sprawy(item_id, contact_id)
                log(f"✅ [{request_id}] Praca removed: {result.get('action')}")
            else:
                # ADD or UPDATE - sync the item
                log(f"🔄 [{request_id}] Syncing Praca item {item_id} to Sprawy...")
                result = praca_sync.sync_praca_to_sprawy(item_id, contact_id)
                log(f"✅ [{request_id}] Praca sync completed: {result.get('action')}")

        elif entity_type_id == SPA_PROCESY:
            # Event from Procesy legalizacyjne (1110) - sync specific item
            log(f"📋 [{request_id}] Event from SPA 1110 (Procesy legalizacyjne)")
            log(f"   Item ID: {item_id}")
            log(f"   Contact ID: {contact_id}")
            log(f"   Bitrix Event: {bitrix_event}")

            if 'DELETE' in (bitrix_event or '').upper():
                log(f"🗑️ [{request_id}] Removing Procesy item {item_id} from Sprawy...")
                result = procesy_sync.remove_procesy_from_sprawy(item_id, contact_id)
                log(f"✅ [{request_id}] Procesy removed: {result.get('action')}")
            else:
                # ADD or UPDATE - sync the item
                log(f"🔄 [{request_id}] Syncing Procesy item {item_id} to Sprawy...")
                result = procesy_sync.sync_procesy_to_sprawy(item_id, contact_id)
                log(f"✅ [{request_id}] Procesy sync completed: {result.get('action')}")

        elif event == 'sync_all':
            # Manual full sync request
            log(f"📋 [{request_id}] Manual FULL SYNC requested")
            log(f"   Contact ID: {contact_id}")

            log(f"")
            log(f"🔄 [{request_id}] Starting manual full sync...")
            result_podstawy = podstawy_sync.sync_all_for_contact(contact_id)
            result_praca = praca_sync.sync_all_praca_for_contact(contact_id)
            result_procesy = procesy_sync.sync_all_for_contact(contact_id)
            result_contact = contact_sync.sync_contact_to_all_sprawy(contact_id)

            result = {
                "action": "manual_sync_all",
                "contact_id": contact_id,
                "podstawy_sync": result_podstawy,
                "praca_sync": result_praca,
                "procesy_sync": result_procesy,
                "contact_sync": result_contact
            }

            log(f"✅ [{request_id}] Manual sync completed")

        else:
            # Fallback: treat as Podstawy pobytu event (legacy behavior)
            log(f"⚠️ [{request_id}] Unknown entity type, using fallback")
            log(f"   Treating as Podstawy pobytu event")

            if event in ('podstawy_created', 'podstawy_updated'):
                result = podstawy_sync.sync_podstawy_to_sprawy(item_id, contact_id)
            elif event == 'podstawy_deleted':
                result = podstawy_sync.remove_podstawy_from_sprawy(item_id, contact_id)
            else:
                result = podstawy_sync.sync_podstawy_to_sprawy(item_id, contact_id)

        # Calculate timing
        sync_time = time.time() - sync_start
        total_time = time.time() - start_time

        log(f"")
        log(f"✅ [{request_id}] Sync completed successfully")
        log(f"   Sync time: {sync_time:.2f}s")
        log(f"   Total time: {total_time:.2f}s")
        log(f"   Result: {result.get('action', 'N/A')}")
        log("=" * 70)

    except Exception as e:
        total_time = time.time() - start_time
        log(f"")
        log(f"❌ [{request_id}] Sync failed: {type(e).__name__}: {e}")
        log(f"   Total time: {total_time:.2f}s")
        log("=" * 70)
        raise  # Retry on sync failure
