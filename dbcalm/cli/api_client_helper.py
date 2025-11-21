"""Shared utilities for CLI commands that interact with the API."""

import time

import requests
import urllib3

from dbcalm.config.config_factory import config_factory
from dbcalm.data.repository.client import ClientRepository
from dbcalm.logger.logger_factory import logger_factory

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Constant for temporary client label
TEMP_CLIENT_LABEL = "temp-system-cron"


class APIError(Exception):
    """Exception raised for API-related errors."""


def get_api_url() -> str:
    """Get the API URL from config.

    Returns:
        API base URL (e.g., "https://localhost:8335")
    """
    config = config_factory()
    host = config.value("api_host", "127.0.0.1")
    port = config.value("api_port", 8335)
    protocol = (
        "https" if config.value("ssl_cert") and config.value("ssl_key") else "http"
    )
    return f"{protocol}://{host}:{port}"


def get_or_create_temp_client() -> tuple[str, str]:
    """Ensure a fresh temporary client exists.

    Deletes any existing temp client and creates a new one.

    Returns:
        Tuple of (client_id, client_secret)
    """
    client_repo = ClientRepository()

    # Get all clients and find the temp one
    clients, _ = client_repo.get_list(None, None, 1, 1000)
    temp_client = next(
        (c for c in clients if c.label == TEMP_CLIENT_LABEL),
        None,
    )

    # Delete if exists
    if temp_client:
        client_repo.delete(temp_client.id)

    # Create new temporary client
    new_client = client_repo.create(TEMP_CLIENT_LABEL)
    return new_client.id, new_client.secret


def cleanup_temp_client(client_id: str) -> None:
    """Delete the temporary client.

    Args:
        client_id: ID of the client to delete
    """
    try:
        client_repo = ClientRepository()
        client_repo.delete(client_id)
    except Exception:
        # Best effort cleanup - don't fail if client doesn't exist
        logger = logger_factory()
        logger.warning("Failed to cleanup temporary client %s", client_id)


def get_bearer_token(client_id: str, client_secret: str) -> str:
    """Authenticate with client credentials and get bearer token.

    Args:
        client_id: Client ID
        client_secret: Client secret

    Returns:
        Bearer token string

    Raises:
        APIError: If authentication fails
    """
    api_url = get_api_url()
    token_url = f"{api_url}/auth/token"

    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }

    try:
        response = requests.post(
            token_url,
            json=data,
            timeout=10,
            verify=False,  # noqa: S501
        )
        response.raise_for_status()
        token_data = response.json()
        return token_data["access_token"]
    except requests.exceptions.RequestException as e:
        msg = f"Failed to authenticate: {e!s}"
        raise APIError(msg) from e


def wait_for_process_completion(
    token: str,
    process_id: int,
    *,
    timeout: int = 600,
) -> dict:
    """Poll process status until completion or timeout.

    Args:
        token: Bearer token for authentication
        process_id: Process ID to monitor
        timeout: Maximum time to wait in seconds

    Returns:
        Final process status dict

    Raises:
        APIError: If process fails or times out
    """
    api_url = get_api_url()
    status_url = f"{api_url}/status/{process_id}"

    headers = {"Authorization": f"Bearer {token}"}

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(
                status_url,
                headers=headers,
                timeout=10,
                verify=False,  # noqa: S501
            )
            response.raise_for_status()
            status = response.json()

            if status.get("status") == "success":
                return status
            if status.get("status") == "failed":
                error_msg = status.get("error", "Unknown error")
                msg = f"Process failed: {error_msg}"
                raise APIError(msg)

            # Still running, wait and retry
            time.sleep(2)

        except requests.exceptions.RequestException as e:
            msg = f"Failed to check process status: {e!s}"
            raise APIError(msg) from e

    msg = f"Process {process_id} timed out after {timeout} seconds"
    raise APIError(msg)
