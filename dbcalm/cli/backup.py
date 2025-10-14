import argparse
import sys

import requests
import urllib3

from dbcalm.config.config_factory import config_factory
from dbcalm.data.repository.client import ClientRepository
from dbcalm.logger.logger_factory import logger_factory

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TEMP_CLIENT_LABEL = "temp-system-cron"


class BackupError(Exception):
    """Exception raised for backup-related errors."""


def get_api_url() -> str:
    """Get the API URL from config."""
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
        Exception: If authentication fails
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
        raise BackupError(msg) from e


def trigger_backup(token: str, backup_type: str) -> dict:
    """Call the backup API endpoint.

    Args:
        token: Bearer token for authentication
        backup_type: Type of backup ("full" or "incremental")

    Returns:
        Response JSON from the API

    Raises:
        Exception: If backup request fails
    """
    api_url = get_api_url()
    backup_url = f"{api_url}/backups"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    data = {"type": backup_type}

    try:
        response = requests.post(
            backup_url,
            json=data,
            headers=headers,
            timeout=30,
            verify=False,  # noqa: S501
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        # Try to get error detail from response
        try:
            error_data = e.response.json()
            error_msg = error_data.get("detail", str(e))
        except Exception:
            error_msg = str(e)
        msg = f"Backup request failed: {error_msg}"
        raise BackupError(msg) from e
    except requests.exceptions.RequestException as e:
        msg = f"Backup request failed: {e!s}"
        raise BackupError(msg) from e


def create_backup(backup_type: str) -> None:
    """Create a backup using temporary client credentials.

    This function:
    1. Creates a temporary client
    2. Authenticates to get a token
    3. Triggers the backup
    4. Cleans up the temporary client
    5. Exits with appropriate status code

    Args:
        backup_type: Type of backup ("full" or "incremental")
    """
    # Validate backup type
    if backup_type not in ["full", "incremental"]:
        print("Error: Invalid backup type. Must be 'full' or 'incremental'")
        sys.exit(1)

    client_id = None

    try:
        # Step 1: Create temporary client
        client_id, client_secret = get_or_create_temp_client()

        # Step 2: Authenticate
        token = get_bearer_token(client_id, client_secret)

        # Step 3: Trigger backup
        response = trigger_backup(token, backup_type)

        # Step 4: Cleanup
        cleanup_temp_client(client_id)

        # Step 5: Success
        pid = response.get("pid", "unknown")
        backup_label = "Full" if backup_type == "full" else "Incremental"
        print(f"Success: {backup_label} backup request accepted (PID: {pid})")
        sys.exit(0)

    except Exception as e:
        # Cleanup on error
        if client_id:
            cleanup_temp_client(client_id)

        print(f"Error: {e!s}")
        sys.exit(1)


def run(args: argparse.Namespace) -> None:
    """Handle backup command execution.

    Args:
        args: Parsed command line arguments
    """
    create_backup(args.backup_type)


def configure_parser(subparsers: argparse._SubParsersAction) -> None:
    """Configure the backup subcommand parser.

    Args:
        subparsers: Subparser action from main argument parser
    """
    backup_parser = subparsers.add_parser(
        "backup",
        help="Create a backup (non-interactive, for cron use)",
    )
    backup_parser.add_argument(
        "backup_type",
        choices=["full", "incremental"],
        help="Type of backup to create",
    )
