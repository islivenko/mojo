"""
Bitrix24 OAuth Token Refresher
Refreshes Bitrix24 OAuth tokens on a schedule via Cloud Scheduler
Stores tokens in Secret Manager with automatic cleanup of old versions

Project: mojo_agency
"""
import os
import time
import requests
import functions_framework
from google.cloud import secretmanager
from google.api_core import exceptions as api_exceptions

# Google Cloud Logging integration
import google.cloud.logging

try:
    client = google.cloud.logging.Client()
    client.setup_logging()
except Exception as e:
    print(f"Warning: Could not setup Cloud Logging: {e}")

import logging
logger = logging.getLogger('b24-token-refresh')
logger.setLevel(logging.DEBUG)

# Configuration (set via --set-env-vars during deploy)
PROJECT_ID = os.getenv("PROJECT_ID")  # Required: set in deploy.sh
B24_CLIENT_ID = os.getenv("B24_CLIENT_ID")  # From Secret Manager
B24_CLIENT_SECRET = os.getenv("B24_CLIENT_SECRET")  # From Secret Manager

# Secret Manager settings
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET", "b24-access-token")
REFRESH_TOKEN_SECRET = os.getenv("REFRESH_TOKEN_SECRET", "b24-refresh-token")

# Log configuration on startup
logger.info("=" * 60)
logger.info("=== B24 Token Refresh initialized (Secret Manager) ===")
logger.info(f"Config: PROJECT_ID={PROJECT_ID}")
logger.info(f"Config: B24_CLIENT_ID={'*' * 10 if B24_CLIENT_ID else 'NOT SET'}")
logger.info(f"Config: B24_CLIENT_SECRET={'*' * 10 if B24_CLIENT_SECRET else 'NOT SET'}")
logger.info(f"Config: ACCESS_TOKEN_SECRET={ACCESS_TOKEN_SECRET}")
logger.info(f"Config: REFRESH_TOKEN_SECRET={REFRESH_TOKEN_SECRET}")


class SecretManagerTokenStore:
    """Bitrix24 token manager using Secret Manager with auto-cleanup"""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self._client = None
        logger.debug(f"SecretManagerTokenStore initialized: project={project_id}")

    @property
    def client(self) -> secretmanager.SecretManagerServiceClient:
        """Lazy initialization of Secret Manager client"""
        if self._client is None:
            logger.debug("Creating Secret Manager client...")
            self._client = secretmanager.SecretManagerServiceClient()
            logger.debug("Secret Manager client created successfully")
        return self._client

    def _get_secret_path(self, secret_name: str, version: str = "latest") -> str:
        """Builds the full secret version path"""
        return f"projects/{self.project_id}/secrets/{secret_name}/versions/{version}"

    def _get_secret_parent(self, secret_name: str) -> str:
        """Builds the secret parent path"""
        return f"projects/{self.project_id}/secrets/{secret_name}"

    def get_secret(self, secret_name: str) -> str:
        """Gets the latest version of a secret"""
        logger.debug(f"Getting secret: {secret_name}")
        start_time = time.time()

        try:
            name = self._get_secret_path(secret_name, "latest")
            response = self.client.access_secret_version(request={"name": name})
            value = response.payload.data.decode("UTF-8")

            elapsed = time.time() - start_time
            logger.info(f"Secret '{secret_name}' retrieved in {elapsed:.2f}s (length: {len(value)})")
            logger.debug(f"Secret preview: {value[:20]}...")

            return value

        except api_exceptions.NotFound:
            logger.error(f"Secret '{secret_name}' not found in project {self.project_id}")
            raise
        except Exception as e:
            logger.error(f"Failed to get secret '{secret_name}': {e}", exc_info=True)
            raise

    def save_secret(self, secret_name: str, value: str) -> str:
        """
        Saves a new version of a secret and deletes old versions.
        Returns the new version name.
        """
        logger.info(f"Saving new version of secret: {secret_name}")
        start_time = time.time()

        parent = self._get_secret_parent(secret_name)

        try:
            # Add new version
            response = self.client.add_secret_version(
                request={
                    "parent": parent,
                    "payload": {"data": value.encode("UTF-8")}
                }
            )

            new_version = response.name
            elapsed = time.time() - start_time
            logger.info(f"Secret version created: {new_version} in {elapsed:.2f}s")

            # Cleanup old versions (keep only the latest)
            self._cleanup_old_versions(secret_name, keep_latest=1)

            return new_version

        except Exception as e:
            logger.error(f"Failed to save secret '{secret_name}': {e}", exc_info=True)
            raise

    def _cleanup_old_versions(self, secret_name: str, keep_latest: int = 1) -> int:
        """
        Destroys old secret versions, keeping only the latest N versions.
        Returns the number of versions destroyed.
        """
        logger.info(f"Cleaning up old versions of '{secret_name}', keeping latest {keep_latest}")
        start_time = time.time()

        parent = self._get_secret_parent(secret_name)

        try:
            # List all versions
            versions = list(self.client.list_secret_versions(request={"parent": parent}))
            logger.debug(f"Found {len(versions)} total versions")

            # Filter enabled versions and sort by creation time (newest first)
            enabled_versions = [
                v for v in versions
                if v.state == secretmanager.SecretVersion.State.ENABLED
            ]
            enabled_versions.sort(key=lambda v: v.create_time, reverse=True)

            logger.debug(f"Found {len(enabled_versions)} enabled versions")

            # Destroy old versions
            destroyed_count = 0
            for version in enabled_versions[keep_latest:]:
                version_id = version.name.split('/')[-1]
                logger.debug(f"Destroying version {version_id}...")

                self.client.destroy_secret_version(request={"name": version.name})
                destroyed_count += 1

            elapsed = time.time() - start_time
            logger.info(f"Cleanup complete: destroyed {destroyed_count} old versions in {elapsed:.2f}s")

            return destroyed_count

        except Exception as e:
            logger.error(f"Failed to cleanup versions for '{secret_name}': {e}", exc_info=True)
            # Don't raise - cleanup failure shouldn't break token refresh
            return 0

    def get_tokens(self) -> dict:
        """Retrieves current tokens from Secret Manager"""
        logger.info("Getting tokens from Secret Manager...")
        start_time = time.time()

        access_token = self.get_secret(ACCESS_TOKEN_SECRET)
        refresh_token = self.get_secret(REFRESH_TOKEN_SECRET)

        elapsed = time.time() - start_time
        logger.info(f"Both tokens retrieved in {elapsed:.2f}s")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }

    def save_tokens(self, tokens: dict) -> None:
        """Saves tokens to Secret Manager with auto-cleanup"""
        logger.info("Saving tokens to Secret Manager...")
        start_time = time.time()

        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")

        if access_token:
            self.save_secret(ACCESS_TOKEN_SECRET, access_token)

        if refresh_token:
            self.save_secret(REFRESH_TOKEN_SECRET, refresh_token)

        elapsed = time.time() - start_time
        logger.info(f"All tokens saved and cleaned up in {elapsed:.2f}s")

    def refresh_tokens(self, client_id: str, client_secret: str) -> dict:
        """Refreshes OAuth tokens via Bitrix24 OAuth server"""
        logger.info("Starting token refresh process...")
        total_start = time.time()

        # Step 1: Get current refresh token
        step_start = time.time()
        refresh_token = self.get_secret(REFRESH_TOKEN_SECRET)

        if not refresh_token:
            logger.error("No refresh_token found in Secret Manager!")
            raise ValueError("No refresh_token found in Secret Manager")

        logger.info(f"Step 1/4: Current refresh token retrieved ({time.time()-step_start:.2f}s)")

        # Step 2: Request new tokens from Bitrix24
        step_start = time.time()
        logger.info("Step 2/4: Requesting new tokens from Bitrix24 OAuth server...")

        payload = {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        }
        logger.debug(f"OAuth request payload: grant_type=refresh_token, client_id={client_id[:10]}...")

        try:
            response = requests.post(
                "https://oauth.bitrix.info/oauth/token/",
                data=payload,
                timeout=30
            )
            logger.debug(f"OAuth response: status={response.status_code}, time={time.time()-step_start:.2f}s")

            response.raise_for_status()
            new_tokens = response.json()

        except requests.RequestException as e:
            logger.error(f"OAuth request failed: {e}", exc_info=True)
            raise

        if "access_token" not in new_tokens:
            logger.error(f"Token refresh failed - no access_token in response: {new_tokens}")
            raise ValueError(f"Token refresh failed: {new_tokens}")

        logger.info(f"Step 2/4: New tokens received ({time.time()-step_start:.2f}s)")
        logger.debug(f"New access_token: {new_tokens.get('access_token', '')[:20]}...")

        # Preserve refresh_token if not returned
        if "refresh_token" not in new_tokens:
            logger.debug("New refresh_token not provided, keeping existing one")
            new_tokens["refresh_token"] = refresh_token

        # Step 3: Save new tokens
        step_start = time.time()
        logger.info("Step 3/4: Saving new tokens to Secret Manager...")
        self.save_tokens(new_tokens)
        logger.info(f"Step 3/4: Tokens saved ({time.time()-step_start:.2f}s)")

        # Step 4: Verify versions count
        step_start = time.time()
        logger.info("Step 4/4: Verifying secret versions...")

        for secret_name in [ACCESS_TOKEN_SECRET, REFRESH_TOKEN_SECRET]:
            parent = self._get_secret_parent(secret_name)
            versions = list(self.client.list_secret_versions(request={"parent": parent}))
            enabled_count = sum(1 for v in versions if v.state == secretmanager.SecretVersion.State.ENABLED)
            logger.info(f"Secret '{secret_name}': {enabled_count} enabled version(s)")

        logger.info(f"Step 4/4: Verification complete ({time.time()-step_start:.2f}s)")

        total_time = time.time() - total_start
        logger.info(f"Token refresh completed successfully! Total time: {total_time:.2f}s")

        return new_tokens


@functions_framework.cloud_event
def main(cloud_event):
    """
    Pub/Sub triggered token refresh handler.
    Called on schedule via Cloud Scheduler.
    """
    start_time = time.time()

    logger.info("=" * 60)
    logger.info("=== TOKEN REFRESH REQUEST RECEIVED ===")
    logger.debug(f"CloudEvent ID: {cloud_event.get('id', 'unknown')}")
    logger.debug(f"CloudEvent source: {cloud_event.get('source', 'unknown')}")

    # Validate configuration
    if not all([PROJECT_ID, B24_CLIENT_ID, B24_CLIENT_SECRET]):
        missing = []
        if not PROJECT_ID: missing.append("PROJECT_ID")
        if not B24_CLIENT_ID: missing.append("B24_CLIENT_ID")
        if not B24_CLIENT_SECRET: missing.append("B24_CLIENT_SECRET")
        error_msg = f"Missing required environment variables: {', '.join(missing)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    try:
        token_store = SecretManagerTokenStore(project_id=PROJECT_ID)
        new_tokens = token_store.refresh_tokens(B24_CLIENT_ID, B24_CLIENT_SECRET)

        total_time = time.time() - start_time
        logger.info(f"✅ Token refresh completed successfully!")
        logger.info(f"Total execution time: {total_time:.2f}s")
        logger.info("=" * 60)

    except api_exceptions.PermissionDenied as e:
        logger.error(f"Permission denied accessing Secret Manager: {e}", exc_info=True)
        raise

    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"❌ Token refresh failed after {total_time:.2f}s: {e}", exc_info=True)
        raise
