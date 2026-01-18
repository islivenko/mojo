"""
B24 SPA 1106 Daily Sync

Scheduled function that runs daily to sync all ACTIVE Sprawy cudzoziemców.
Publishes individual messages to Pub/Sub for each Sprawy,
allowing the worker to process them in parallel.

Triggered by: Cloud Scheduler (daily at 03:00 Warsaw time)

Flow:
1. Fetch all ACTIVE Sprawy cudzoziemców (not in final stages)
2. For each: publish message to Pub/Sub topic
3. Worker processes each item individually

Project: mojo-478621
"""

import os
import sys
import json
import logging
import time
import functions_framework
from flask import Request
from google.cloud import pubsub_v1, secretmanager
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger('b24-spa-1106-daily-sync')


def log(msg):
    """Log message to Cloud Logging."""
    logger.info(msg)


# Configuration
PROJECT_ID = os.getenv("PROJECT_ID", "mojo-478621")
TOPIC_NAME = os.getenv("TOPIC_NAME", "b24-spa-1106-sync-events")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET", "b24-access-token")
B24_DOMAIN = os.getenv("B24_DOMAIN", "mojo.bitrix24.pl")
SPA_SPRAWY = int(os.getenv("SPA_SPRAWY_ID", "1106"))

# Final stages - items in these stages are NOT active
FINAL_STAGES = {'SUCCESS', 'FAIL', 'FAILURE', 'LOSE', 'APOLOGY'}

# Lazy init clients
_publisher = None
_secret_client = None
_access_token = None


def get_publisher():
    """Get or create Pub/Sub publisher client."""
    global _publisher
    if _publisher is None:
        _publisher = pubsub_v1.PublisherClient()
    return _publisher


def get_access_token() -> str:
    """Get access token from Secret Manager."""
    global _secret_client, _access_token

    if _access_token:
        return _access_token

    if _secret_client is None:
        _secret_client = secretmanager.SecretManagerServiceClient()

    secret_path = f"projects/{PROJECT_ID}/secrets/{ACCESS_TOKEN_SECRET}/versions/latest"
    response = _secret_client.access_secret_version(name=secret_path)
    _access_token = response.payload.data.decode("UTF-8")

    return _access_token


def is_active_stage(stage_id: str) -> bool:
    """
    Check if stageId represents an active (non-final) stage.

    Args:
        stage_id: Bitrix24 stageId (e.g., DT1106_52:NEW)

    Returns:
        True if stage is active (not final)
    """
    if not stage_id:
        return True

    parts = stage_id.split(':')
    if len(parts) < 2:
        return True

    stage_name = parts[-1].upper()
    return stage_name not in FINAL_STAGES


def get_all_active_sprawy() -> list:
    """
    Fetch all ACTIVE Sprawy cudzoziemców from Bitrix24.

    Returns:
        List of active Sprawy items
    """
    log("📋 Fetching all Sprawy cudzoziemców from Bitrix24...")

    token = get_access_token()
    base_url = f"https://{B24_DOMAIN}/rest"

    all_items = []
    start = 0

    while True:
        response = requests.post(
            f"{base_url}/crm.item.list.json",
            data={
                'auth': token,
                'entityTypeId': SPA_SPRAWY,
                'select[0]': 'id',
                'select[1]': 'title',
                'select[2]': 'stageId',
                'select[3]': 'contactId',
                'start': start
            },
            timeout=30
        )

        data = response.json()

        if 'error' in data:
            log(f"❌ API Error: {data.get('error')} - {data.get('error_description', '')}")
            break

        result = data.get('result', {})
        items = result.get('items', [])
        all_items.extend(items)

        log(f"   Fetched {len(items)} items (total: {len(all_items)})")

        # Check for more pages
        next_start = data.get('next')
        if next_start:
            start = next_start
        else:
            break

    # Filter only active items
    active_items = [item for item in all_items if is_active_stage(item.get('stageId', ''))]

    log(f"📊 Total: {len(all_items)}, Active: {len(active_items)}")

    return active_items


def publish_sync_messages(items: list) -> int:
    """
    Publish sync message for each Sprawy to Pub/Sub.

    Args:
        items: List of Sprawy items to sync

    Returns:
        Number of messages published
    """
    if not items:
        log("⚠️ No items to sync")
        return 0

    publisher = get_publisher()
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_NAME)

    log(f"📤 Publishing {len(items)} messages to Pub/Sub...")

    published = 0
    futures = []

    for item in items:
        message = {
            "event": "daily_sync",
            "id": str(item['id']),
            "contact_id": str(item.get('contactId', '')) if item.get('contactId') else None,
            "entity_type_id": str(SPA_SPRAWY),
            "is_contact_event": False,
            "bitrix_event": "DAILY_SYNC",
            "timestamp": time.time()
        }

        message_data = json.dumps(message).encode('utf-8')
        future = publisher.publish(topic_path, message_data)
        futures.append((item['id'], future))

    # Wait for all publishes to complete
    for item_id, future in futures:
        try:
            future.result(timeout=10)
            published += 1
        except Exception as e:
            log(f"❌ Failed to publish for item {item_id}: {e}")

    log(f"✅ Published {published}/{len(items)} messages")

    return published


@functions_framework.http
def main(request: Request):
    """
    Daily sync job - triggered by Cloud Scheduler.

    Fetches all active Sprawy cudzoziemców and publishes sync messages
    for each to Pub/Sub for parallel processing by the worker.
    """
    start_time = time.time()

    log("=" * 60)
    log("=== B24 SPA 1106 DAILY SYNC STARTED ===")
    log("=" * 60)

    try:
        # Get all active Sprawy
        active_items = get_all_active_sprawy()

        if not active_items:
            log("ℹ️ No active Sprawy found - nothing to sync")
            return {
                "status": "ok",
                "message": "No active items to sync",
                "total": 0,
                "elapsed_ms": round((time.time() - start_time) * 1000)
            }, 200

        # Log items to sync
        log("")
        log("📋 Items to sync:")
        for item in active_items[:10]:  # Log first 10
            contact_id = item.get('contactId', 'N/A')
            log(f"   - ID={item['id']}: {item.get('title', 'N/A')} (contact: {contact_id})")
        if len(active_items) > 10:
            log(f"   ... and {len(active_items) - 10} more")

        # Publish sync messages
        published = publish_sync_messages(active_items)

        elapsed = (time.time() - start_time) * 1000

        log("")
        log("=" * 60)
        log("=== DAILY SYNC COMPLETED ===")
        log(f"   Total active: {len(active_items)}")
        log(f"   Published: {published}")
        log(f"   Duration: {elapsed:.0f}ms")
        log("=" * 60)

        return {
            "status": "ok",
            "total_active": len(active_items),
            "published": published,
            "elapsed_ms": round(elapsed)
        }, 200

    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        log(f"❌ Daily sync failed: {e}")

        return {
            "status": "error",
            "message": str(e),
            "elapsed_ms": round(elapsed)
        }, 500


@functions_framework.http
def health(request: Request):
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "b24-spa-1106-daily-sync",
        "project": PROJECT_ID
    }, 200
