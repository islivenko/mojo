"""
Bitrix24 REST API Client

Provides authenticated access to Bitrix24 REST API with Secret Manager integration.
"""

import logging
import time
import requests
from typing import Optional, Dict, List, Any
from google.cloud import secretmanager

logger = logging.getLogger('b24-api')


class BitrixAPI:
    """Bitrix24 REST API client with Secret Manager token retrieval."""

    def __init__(self, domain: str, project_id: str, access_token_secret: str):
        """
        Initialize Bitrix24 API client.

        Args:
            domain: Bitrix24 portal domain (e.g., mojo.bitrix24.pl)
            project_id: GCP Project ID for Secret Manager
            access_token_secret: Secret name for access token
        """
        self.domain = domain
        self.base_url = f"https://{domain}/rest"
        self.project_id = project_id
        self.access_token_secret = access_token_secret
        self._access_token: Optional[str] = None
        self._secret_client: Optional[secretmanager.SecretManagerServiceClient] = None

        logger.info(f"🔧 BitrixAPI initialized: domain={domain}, project={project_id}")

    @property
    def secret_client(self) -> secretmanager.SecretManagerServiceClient:
        """Lazy initialization of Secret Manager client."""
        if self._secret_client is None:
            logger.debug("📦 Initializing Secret Manager client...")
            self._secret_client = secretmanager.SecretManagerServiceClient()
        return self._secret_client

    def _get_access_token(self) -> str:
        """Get access token from Secret Manager."""
        if self._access_token:
            return self._access_token

        logger.info(f"🔑 Fetching access token from Secret Manager: {self.access_token_secret}")
        secret_path = f"projects/{self.project_id}/secrets/{self.access_token_secret}/versions/latest"

        start = time.time()
        response = self.secret_client.access_secret_version(name=secret_path)
        self._access_token = response.payload.data.decode("UTF-8")
        duration = (time.time() - start) * 1000

        logger.info(f"🔑 Access token retrieved ({duration:.0f}ms)")
        return self._access_token

    def _call(self, method: str, params: Optional[Dict] = None) -> Dict:
        """
        Make API call to Bitrix24.

        Args:
            method: API method name (e.g., crm.item.get)
            params: Request parameters

        Returns:
            API response result

        Raises:
            Exception: If API call fails
        """
        url = f"{self.base_url}/{method}.json"
        params = params or {}
        params['auth'] = self._get_access_token()

        # Log request (without auth token)
        log_params = {k: v for k, v in params.items() if k != 'auth'}
        logger.info(f"📤 API Request: {method}")
        logger.debug(f"   Params: {log_params}")

        start = time.time()
        try:
            response = requests.post(url, data=params, timeout=30)
            duration = (time.time() - start) * 1000

            response.raise_for_status()
            data = response.json()

            if 'error' in data:
                error = data.get('error', 'Unknown error')
                error_desc = data.get('error_description', '')
                logger.error(f"❌ API Error [{method}]: {error} - {error_desc} ({duration:.0f}ms)")
                raise Exception(f"Bitrix24 API error: {error} - {error_desc}")

            logger.info(f"📥 API Response: {method} ✅ ({duration:.0f}ms)")
            return data.get('result', data)

        except requests.exceptions.Timeout:
            logger.error(f"⏱️ API Timeout [{method}]: Request exceeded 30s")
            raise
        except requests.exceptions.RequestException as e:
            duration = (time.time() - start) * 1000
            logger.error(f"❌ API Request Failed [{method}]: {e} ({duration:.0f}ms)")
            raise

    # ========================
    # Contact Methods
    # ========================

    def get_contact(self, contact_id: int) -> Dict:
        """Get contact by ID."""
        logger.info(f"👤 Getting contact ID={contact_id}")
        result = self._call('crm.contact.get', {'id': contact_id})
        logger.debug(f"   Contact: {result.get('NAME', '')} {result.get('LAST_NAME', '')}")
        return result

    # ========================
    # SPA Item Methods
    # ========================

    def get_item(self, entity_type_id: int, item_id: int) -> Dict:
        """Get SPA item by ID."""
        logger.info(f"📋 Getting SPA item: entityTypeId={entity_type_id}, id={item_id}")
        result = self._call('crm.item.get', {
            'entityTypeId': entity_type_id,
            'id': item_id
        })
        item = result.get('item', result)
        logger.debug(f"   Item: title={item.get('title', 'N/A')}, stageId={item.get('stageId', 'N/A')}")
        return item

    def list_items(
        self,
        entity_type_id: int,
        filter: Optional[Dict] = None,
        select: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        List SPA items with filter.

        Args:
            entity_type_id: SPA entity type ID
            filter: Filter conditions
            select: Fields to select
            limit: Maximum items to return

        Returns:
            List of items
        """
        logger.info(f"📋 Listing SPA items: entityTypeId={entity_type_id}, filter={filter}")

        params = {
            'entityTypeId': entity_type_id,
            'start': 0
        }

        # Build filter params
        if filter:
            for key, value in filter.items():
                params[f'filter[{key}]'] = value

        # Build select params
        if select:
            for i, field in enumerate(select):
                params[f'select[{i}]'] = field

        result = self._call('crm.item.list', params)
        items = result.get('items', [])

        logger.info(f"   Found {len(items)} items")
        for item in items:
            logger.debug(f"   - ID={item.get('id')}: {item.get('title', 'N/A')}")

        return items

    def update_item(self, entity_type_id: int, item_id: int, fields: Dict) -> Dict:
        """
        Update SPA item.

        Args:
            entity_type_id: SPA entity type ID
            item_id: Item ID to update
            fields: Fields to update

        Returns:
            Updated item
        """
        logger.info(f"✏️ Updating SPA item: entityTypeId={entity_type_id}, id={item_id}")
        logger.info(f"   Fields: {fields}")

        params = {
            'entityTypeId': entity_type_id,
            'id': item_id
        }

        # Build fields params
        for key, value in fields.items():
            if isinstance(value, list):
                if len(value) == 0:
                    # Empty array - Bitrix24 requires explicit empty value
                    params[f'fields[{key}]'] = ''
                    logger.info(f"   Clearing field {key} (empty array)")
                else:
                    for i, v in enumerate(value):
                        params[f'fields[{key}][{i}]'] = v
            else:
                params[f'fields[{key}]'] = value

        result = self._call('crm.item.update', params)
        logger.info(f"✅ Item {item_id} updated successfully")
        return result.get('item', result)

    def add_item(self, entity_type_id: int, fields: Dict) -> Dict:
        """
        Create new SPA item.

        Args:
            entity_type_id: SPA entity type ID
            fields: Item fields

        Returns:
            Created item
        """
        logger.info(f"➕ Creating SPA item: entityTypeId={entity_type_id}")
        logger.debug(f"   Fields: {fields}")

        params = {
            'entityTypeId': entity_type_id
        }

        # Build fields params
        for key, value in fields.items():
            if isinstance(value, list):
                for i, v in enumerate(value):
                    params[f'fields[{key}][{i}]'] = v
            else:
                params[f'fields[{key}]'] = value

        result = self._call('crm.item.add', params)
        item = result.get('item', result)
        logger.info(f"✅ Item created: ID={item.get('id')}")
        return item
