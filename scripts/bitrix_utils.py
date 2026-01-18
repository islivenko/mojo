import json
import os
import re
from typing import Any, Dict, List
from urllib.parse import urljoin
from dotenv import load_dotenv

import requests

# Load .env from the project root. Assumes this script is in a subdirectory.
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
elif os.path.exists('.env'):
     load_dotenv()


REQUEST_TIMEOUT = float(os.getenv("BITRIX_REQUEST_TIMEOUT", "10"))


def _ensure_protocol(url: str) -> str:
    return url if url.startswith(("http://", "https://")) else f"https://{url}"


def _normalized_base(var_name: str) -> str | None:
    value = os.getenv(var_name)
    if not value:
        return None
    return value.rstrip("/") + "/"


WEBHOOK_GET_BASE = _normalized_base("BITRIX_WEBHOOK_GET")
WEBHOOK_POST_BASE = _normalized_base("BITRIX_WEBHOOK_POST") or WEBHOOK_GET_BASE


def _make_bitrix_api_call(
    method: str,
    params: dict | None,
    auth: str | None,
    *,
    http_method: str = "POST",
    unwrap_result: bool = True,
) -> Any:
    """
    Call Bitrix24 either via webhook (preferred) or direct REST endpoint with auth token.

    Args:
        method: API method name, e.g. 'crm.item.get'
        params: Parameters for the call (dict)
        auth: Access token if webhooks are not configured
        http_method: 'GET' or 'POST' for webhook calls (default POST)
    """
    params = params or {}
    http_method = http_method.upper()

    # Primary path: use webhooks if configured
    base = WEBHOOK_POST_BASE if http_method == "POST" else WEBHOOK_GET_BASE
    if not base:
        print("❌ ERROR: BITRIX_WEBHOOK_GET/POST not found in environment. Check your .env file.")
        return None

    url = urljoin(base, f"{method}.json")
    try:
        if http_method == "POST":
            response = requests.post(url, json=params, timeout=REQUEST_TIMEOUT)
        else:
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            print(f"❌ API Error for method {method}: {data.get('error_description', data['error'])}")
            return None
        if unwrap_result:
            return data.get("result", data)
        return data
    except requests.RequestException as exc:
        print(f"❌ HTTP Request Error for method {method}: {exc}")
        return None
    except ValueError:
        print(f"❌ JSON Decode Error for method {method}. Response text: {response.text}")
        return None


def get_smart_item(item_id: int, entity_type_id: int, auth: str | None = None):
    """Fetches a single smart process item."""
    method = "crm.item.get"
    params = {"entityTypeId": entity_type_id, "id": item_id}
    return _make_bitrix_api_call(method, params, auth)


def get_company(company_id: int, auth: str | None = None):
    """Fetches company details."""
    method = "crm.company.get"
    params = {"id": company_id}
    return _make_bitrix_api_call(method, params, auth)


def get_company_requisites(company_id: int, auth: str | None = None):
    """Fetches a list of requisites for a company."""
    method = "crm.requisite.list"
    params = {"filter": {"ENTITY_TYPE_ID": 4, "ENTITY_ID": company_id}}
    return _make_bitrix_api_call(method, params, auth)


def get_company_addresses(company_id: int, auth: str | None = None):
    """Fetches a list of addresses for a company."""
    method = "crm.address.list"
    params = {"filter": {"ENTITY_TYPE_ID": 4, "ENTITY_ID": company_id}}
    return _make_bitrix_api_call(method, params, auth)


def get_contact(contact_id: int, auth: str | None = None):
    """Fetches contact details."""
    method = "crm.contact.get"
    params = {"id": contact_id}
    # Return all fields, including custom ones
    result = _make_bitrix_api_call(method, params, auth)
    if not result:
        return None
    # The result of a 'get' call is nested inside an 'item' key
    return result.get('item', result)


def update_contact(contact_id: int, fields: dict, auth: str | None = None):
    """Updates a contact with new field values."""
    method = "crm.contact.update"
    params = {"id": contact_id, "fields": fields}
    return _make_bitrix_api_call(method, params, auth, http_method="POST")

# --- Field Inspection Functions ---

def get_contact_fields(auth: str | None = None):
    """Fetches the description of all contact fields."""
    method = "crm.contact.fields"
    return _make_bitrix_api_call(method, {}, auth)


def get_company_fields(auth: str | None = None):
    """Fetches the description of all company fields."""
    method = "crm.company.fields"
    return _make_bitrix_api_call(method, {}, auth)


def get_smart_process_fields(entity_type_id: int, auth: str | None = None):
    """Fetches the description of fields for a specific smart process."""
    method = "crm.item.fields"
    params = {"entityTypeId": entity_type_id}
    return _make_bitrix_api_call(method, params, auth)

def get_deal_fields(auth: str | None = None):
    """Fetches the description of all deal fields."""
    method = "crm.deal.fields"
    return _make_bitrix_api_call(method, {}, auth)


def get_smart_process_type_fields(entity_type_id: int, auth: str | None = None):
    """Fetches the description of fields for a specific smart process type."""
    method = "crm.type.fields"
    params = {"entityTypeId": entity_type_id}
    return _make_bitrix_api_call(method, params, auth)

def get_all_smart_process_fields(entity_type_id: int, auth: str | None = None):
    """
    Fetches both system (type) and custom (item) fields for a smart process
    and merges them.
    """
    print(f"   - Fetching system fields for SP {entity_type_id}...")
    type_data = get_smart_process_type_fields(entity_type_id, auth)
    system_fields = type_data.get("fields", {}) if type_data else {}

    print(f"   - Fetching custom fields for SP {entity_type_id}...")
    item_fields = get_smart_process_fields(entity_type_id, auth)

    # The item_fields result is just the dictionary of fields, not nested.
    if not isinstance(item_fields, dict):
        item_fields = {}

    # Merge them, with item_fields taking precedence for any overlapping keys
    return {**system_fields, **item_fields}

def list_smart_items(
    entity_type_id: int,
    filter_params: Dict[str, Any] | None = None,
    select: List[str] | None = None,
    auth: str | None = None,
) -> List[Dict[str, Any]]:
    """
    Fetches smart process items with optional filter/selection, handling pagination.
    """
    items: List[Dict[str, Any]] = []
    start_token: int | None = None

    while True:
        params: Dict[str, Any] = {"entityTypeId": entity_type_id}
        if filter_params:
            params["filter"] = filter_params
        if select:
            params["select"] = select
        if start_token is not None:
            params["start"] = start_token

        payload = _make_bitrix_api_call(
            "crm.item.list",
            params,
            auth,
            http_method="POST",
            unwrap_result=False,
        )
        if not payload:
            break

        result = payload.get("result", {})
        batch = result.get("items", [])
        next_token = result.get("next")

        if batch:
            items.extend(batch)

        if next_token is None:
            break
        start_token = next_token

    return items

def get_disk_file(file_id: int, auth: str | None = None):
    """Fetches metadata for a file on the Bitrix24 disk."""
    method = "disk.file.get"
    params = {"id": file_id}
    return _make_bitrix_api_call(method, params, auth)


def update_smart_item(item_id: int, entity_type_id: int, fields: dict, auth: str | None = None):
    """Updates a smart process item with new field values."""
    method = "crm.item.update"
    params = {"entityTypeId": entity_type_id, "id": item_id, "fields": fields}
    return _make_bitrix_api_call(method, params, auth, http_method="POST")


def list_deals(
    filter_params: Dict[str, Any] | None = None,
    select: List[str] | None = None,
    auth: str | None = None,
) -> List[Dict[str, Any]]:
    """
    Fetches deals with optional filter/selection, handling pagination automatically.
    """
    deals: List[Dict[str, Any]] = []
    start_token: int | None = None

    while True:
        params: Dict[str, Any] = {}
        if filter_params:
            params["filter"] = filter_params
        if select:
            params["select"] = select
        if start_token is not None:
            params["start"] = start_token

        payload = _make_bitrix_api_call(
            "crm.deal.list",
            params,
            auth,
            http_method="POST",
            unwrap_result=False,
        )
        if not payload:
            break

        result = payload.get("result", [])
        if isinstance(result, dict):
            batch = result.get("items", [])
            next_token = result.get("next")
        else:
            batch = result or []
            next_token = payload.get("next")

        if batch:
            deals.extend(batch)

        if next_token is None:
            break
        start_token = next_token

    return deals


def get_deal(deal_id: int, auth: str | None = None):
    """Fetches a single deal by ID."""
    method = "crm.deal.get"
    params = {"id": deal_id}
    result = _make_bitrix_api_call(method, params, auth, http_method="GET")
    if not result:
        return None
    return result.get('item', result)


def update_deal(deal_id: int, fields: dict, auth: str | None = None):
    """Updates deal fields."""
    method = "crm.deal.update"
    params = {"id": deal_id, "fields": fields}
    return _make_bitrix_api_call(method, params, auth, http_method="POST")

def list_user_fields(entity_id: str, auth: str | None = None) -> List[Dict[str, Any]]:
    """Fetches all user fields for a given entity ID."""
    method = "crm.userfield.list"
    params = {
        "order": {"SORT": "ASC"},
        "filter": {"ENTITY_ID": entity_id}
    }
    return _make_bitrix_api_call(method, params, auth, http_method="POST")

def list_deal_categories(auth: str | None = None) -> List[Dict[str, Any]]:
    """Fetches all deal categories (pipelines)."""
    method = "crm.dealcategory.list"
    params = {"order": {"sort": "ASC"}}
    return _make_bitrix_api_call(method, params, auth, http_method="POST")

def create_smart_item(entity_type_id: int, fields: dict, auth: str | None = None):
    """Creates a new smart process item."""
    method = "crm.item.add"
    params = {"entityTypeId": entity_type_id, "fields": fields}
    return _make_bitrix_api_call(method, params, auth, http_method="POST")

def sanitize_for_filename(text: str) -> str:
    """Очищает строку, чтобы она была безопасной для использования в качестве имени файла."""
    text = text.lower()
    # Заменяем пробелы и прочие нежелательные символы на дефис
    text = re.sub(r'[\s._/\\|]+', '-', text)
    # Удаляем все, что не является буквой, цифрой или дефисом
    text = re.sub(r'[^a-z0-9-]', '', text)
    # Сжимаем множественные дефисы в один
    text = re.sub(r'--+', '-', text)
    # Удаляем дефисы в начале и в конце
    text = text.strip('-')
    return text
