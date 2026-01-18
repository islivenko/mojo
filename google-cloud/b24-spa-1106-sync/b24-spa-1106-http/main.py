"""
B24 SPA 1106 Webhook Handler
Lightweight HTTP handler for Bitrix24 Automation webhooks.
Publishes events to Pub/Sub for async processing.

Project: mojo_agency
Handles:
- SPA: Sprawy cudzoziemców (1106)
- Related SPAs: Podstawy pobytu (1042) / Praca (1046) / Procesy legalizacyjne (1110) / Klient/Projekt (1098)
- Contact events: ONCRMCONTACTADD, ONCRMCONTACTUPDATE, ONCRMCONTACTDELETE
"""

import os
import json
import logging
import time
from urllib.parse import parse_qs
import functions_framework
from flask import Request
from google.cloud import pubsub_v1

# Configure logging for Cloud Run
import sys
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger('b24-spa-1106-webhook-handler')
logger.setLevel(logging.INFO)

def log(msg):
    """Log message to Cloud Logging."""
    logger.info(msg)

# Configuration
PROJECT_ID = os.getenv("PROJECT_ID")
TOPIC_NAME = os.getenv("TOPIC_NAME", "b24-spa-1106-sync-events")

# Lazy init publisher
_publisher = None


def get_publisher():
    """Get or create Pub/Sub publisher client."""
    global _publisher
    if _publisher is None:
        _publisher = pubsub_v1.PublisherClient()
    return _publisher


def log_request_details(request: Request) -> dict:
    """Log and return all request details for debugging."""
    details = {
        "method": request.method,
        "path": request.path,
        "url": request.url,
        "content_type": request.content_type,
        "content_length": request.content_length,
        "args": dict(request.args),
        "headers": {k: v for k, v in request.headers if k.lower() not in ['authorization', 'cookie']}
    }

    # Get raw body
    try:
        raw_body = request.get_data(as_text=True)
        details["raw_body"] = raw_body[:1000] if raw_body else None
        details["raw_body_length"] = len(raw_body) if raw_body else 0
    except Exception as e:
        details["raw_body_error"] = str(e)

    # Parse form data
    try:
        if request.form:
            details["form_data"] = dict(request.form)
    except Exception as e:
        details["form_data_error"] = str(e)

    # Parse JSON body
    try:
        if request.is_json:
            details["json_body"] = request.get_json(silent=True)
    except Exception as e:
        details["json_body_error"] = str(e)

    return details


def parse_bitrix_webhook(request: Request) -> dict:
    """
    Parse Bitrix24 webhook data from various formats.

    Bitrix24 can send webhooks in different formats:
    - Query params: ?event=xxx&id=123
    - Form data (application/x-www-form-urlencoded)
    - JSON body
    - Mixed (query params + body)

    Handles:
    - SPA events: ONCRMDYNAMICITEMADD/UPDATE/DELETE
    - Contact events: ONCRMCONTACTADD/UPDATE/DELETE
    """
    result = {
        "event": None,
        "id": None,
        "contact_id": None,
        "entity_type_id": None,
        "bitrix_event": None,
        "is_contact_event": False,
        "bitrix_data": {}
    }

    # 1. Check query params
    result["event"] = request.args.get('event')
    result["id"] = request.args.get('id')
    result["contact_id"] = request.args.get('contact_id')
    result["entity_type_id"] = request.args.get('entity_type_id')

    # 2. Check form data (Bitrix24 standard webhook format)
    if request.form:
        form = dict(request.form)

        # Bitrix24 sends: event, data[FIELDS][ID], auth[application_token], etc.
        result["bitrix_event"] = form.get('event')

        # Extract ID from various possible locations
        if not result["id"]:
            result["id"] = (
                form.get('data[FIELDS][ID]') or
                form.get('id') or
                form.get('ID')
            )

        # Extract CONTACT_ID
        if not result["contact_id"]:
            result["contact_id"] = (
                form.get('data[FIELDS][CONTACT_ID]') or
                form.get('data[FIELDS][contactId]') or
                form.get('contact_id') or
                form.get('CONTACT_ID')
            )

        # Extract ENTITY_TYPE_ID (SPA type: 1106=Sprawy, 1042=Podstawy, 1046=Praca, 1110=Procesy)
        if not result["entity_type_id"]:
            result["entity_type_id"] = (
                form.get('data[FIELDS][ENTITY_TYPE_ID]') or
                form.get('entity_type_id') or
                form.get('ENTITY_TYPE_ID')
            )

        # Store all Bitrix data
        result["bitrix_data"] = form

    # 3. Try parsing raw body as form data (sometimes Flask doesn't parse it)
    try:
        raw_body = request.get_data(as_text=True)
        if raw_body and '=' in raw_body and not request.is_json:
            parsed = parse_qs(raw_body)
            # parse_qs returns lists, take first value
            for key, value in parsed.items():
                if isinstance(value, list) and len(value) > 0:
                    parsed[key] = value[0]

            if not result["id"]:
                result["id"] = parsed.get('data[FIELDS][ID]') or parsed.get('id')
            if not result["contact_id"]:
                result["contact_id"] = parsed.get('data[FIELDS][CONTACT_ID]') or parsed.get('data[FIELDS][contactId]')
            if not result["entity_type_id"]:
                result["entity_type_id"] = parsed.get('data[FIELDS][ENTITY_TYPE_ID]')
            if not result["bitrix_event"]:
                result["bitrix_event"] = parsed.get('event')

            result["bitrix_data"].update(parsed)
    except Exception:
        pass

    # 4. Check JSON body
    if request.is_json:
        try:
            json_data = request.get_json(silent=True) or {}
            result["event"] = result["event"] or json_data.get('event')
            result["id"] = result["id"] or json_data.get('id')
            result["contact_id"] = result["contact_id"] or json_data.get('contact_id')
            result["entity_type_id"] = result["entity_type_id"] or json_data.get('entity_type_id')
            result["bitrix_data"].update(json_data)
        except Exception:
            pass

    # Detect Contact events
    bitrix_event = result["bitrix_event"] or ""
    bitrix_event_upper = bitrix_event.upper()

    if "ONCRMCONTACT" in bitrix_event_upper:
        # Contact event: ONCRMCONTACTADD, ONCRMCONTACTUPDATE, ONCRMCONTACTDELETE
        result["is_contact_event"] = True

        # For Contact events, the ID is the contact_id
        if result["id"] and not result["contact_id"]:
            result["contact_id"] = result["id"]

        # Set event type
        if "ADD" in bitrix_event_upper:
            result["event"] = "contact_created"
        elif "DELETE" in bitrix_event_upper:
            result["event"] = "contact_deleted"
        else:
            result["event"] = "contact_updated"

        # Contact events don't have entity_type_id, use special marker
        result["entity_type_id"] = "CONTACT"

    else:
        # SPA event: ONCRMDYNAMICITEMADD/UPDATE/DELETE
        result["is_contact_event"] = False

        # Set defaults for event
        if not result["event"]:
            if "ADD" in bitrix_event_upper:
                result["event"] = "sprawy_created"
            elif "DELETE" in bitrix_event_upper:
                result["event"] = "sprawy_deleted"
            else:
                result["event"] = "sprawy_updated"

        # Default entity_type_id for SPA events (1106 = Sprawy cudzoziemców)
        if not result["entity_type_id"]:
            result["entity_type_id"] = "1106"

    return result


@functions_framework.http
def main(request: Request):
    """
    HTTP webhook handler for Bitrix24 SPA events.

    Receives webhook from Bitrix24 Automation/BizProc and publishes to Pub/Sub.
    Returns 200 OK immediately for fast response.
    """
    start_time = time.time()
    request_id = f"{int(start_time * 1000)}"

    log(f"{'='*60}")
    log(f"[{request_id}] === B24 SPA 1106 WEBHOOK RECEIVED ===")
    log(f"{'='*60}")

    # Log full request details
    request_details = log_request_details(request)
    log(f"[{request_id}] Request details: {json.dumps(request_details, ensure_ascii=False, default=str)}")

    # Parse Bitrix24 webhook
    parsed = parse_bitrix_webhook(request)
    log(f"[{request_id}] Parsed webhook: {json.dumps(parsed, ensure_ascii=False, default=str)}")

    event = parsed["event"]
    item_id = parsed["id"]
    contact_id = parsed["contact_id"]
    entity_type_id = parsed["entity_type_id"]

    is_contact_event = parsed.get("is_contact_event", False)
    log(f"[{request_id}] Extracted: event={event}, id={item_id}, contact_id={contact_id}, entity_type_id={entity_type_id}, is_contact_event={is_contact_event}")

    # Validate
    if is_contact_event:
        # Contact events need contact_id
        if not contact_id:
            log(f"[{request_id}] ❌ Contact event missing contact_id")
            elapsed = (time.time() - start_time) * 1000
            log(f"[{request_id}] Request completed in {elapsed:.0f}ms with error")
            return {"status": "error", "message": "Contact event requires contact_id", "request_id": request_id}, 400
    else:
        # SPA events need item_id
        if not item_id and event != 'sync_all':
            log(f"[{request_id}] ❌ Missing id parameter")
            elapsed = (time.time() - start_time) * 1000
            log(f"[{request_id}] Request completed in {elapsed:.0f}ms with error")
            return {"status": "error", "message": "Missing id parameter", "request_id": request_id}, 400

        if event == 'sync_all' and not contact_id:
            log(f"[{request_id}] ❌ sync_all requires contact_id")
            elapsed = (time.time() - start_time) * 1000
            log(f"[{request_id}] Request completed in {elapsed:.0f}ms with error")
            return {"status": "error", "message": "sync_all requires contact_id", "request_id": request_id}, 400

    # Build message for Pub/Sub
    message = {
        "event": event,
        "id": item_id,
        "contact_id": contact_id,
        "entity_type_id": entity_type_id,
        "is_contact_event": is_contact_event,
        "request_id": request_id,
        "bitrix_event": parsed.get("bitrix_event"),
        "timestamp": start_time
    }

    log(f"[{request_id}] 📤 Publishing to Pub/Sub topic: {TOPIC_NAME}")
    log(f"[{request_id}] Message: {json.dumps(message, ensure_ascii=False, default=str)}")

    # Publish to Pub/Sub
    try:
        publisher = get_publisher()
        topic_path = publisher.topic_path(PROJECT_ID, TOPIC_NAME)

        message_data = json.dumps(message).encode('utf-8')
        future = publisher.publish(topic_path, message_data)
        message_id = future.result(timeout=10)

        elapsed = (time.time() - start_time) * 1000
        log(f"[{request_id}] ✅ Published to Pub/Sub: message_id={message_id}")
        log(f"[{request_id}] Request completed successfully in {elapsed:.0f}ms")

        return {
            "status": "accepted",
            "message_id": message_id,
            "request_id": request_id,
            "event": event,
            "id": item_id,
            "elapsed_ms": round(elapsed)
        }, 200

    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        log(f"[{request_id}] ❌ Failed to publish to Pub/Sub: {e}")
        log(f"[{request_id}] Request completed with error in {elapsed:.0f}ms")
        return {"status": "error", "message": str(e), "request_id": request_id}, 500


@functions_framework.http
def health(request: Request):
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "b24-spa-1106-webhook-handler",
        "project": PROJECT_ID,
        "topic": TOPIC_NAME
    }, 200
