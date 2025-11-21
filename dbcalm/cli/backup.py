import argparse
import sys

import requests

from dbcalm.cli.api_client_helper import (
    APIError,
    cleanup_temp_client,
    get_api_url,
    get_bearer_token,
    get_or_create_temp_client,
)


def trigger_backup(
    token: str,
    backup_type: str,
    schedule_id: int | None = None,
) -> dict:
    """Call the backup API endpoint.

    Args:
        token: Bearer token for authentication
        backup_type: Type of backup ("full" or "incremental")
        schedule_id: Optional schedule ID that triggered this backup

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
    if schedule_id is not None:
        data["schedule_id"] = schedule_id

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
        raise APIError(msg) from e
    except requests.exceptions.RequestException as e:
        msg = f"Backup request failed: {e!s}"
        raise APIError(msg) from e


def create_backup(backup_type: str, schedule_id: int | None = None) -> None:
    """Create a backup using temporary client credentials.

    This function:
    1. Creates a temporary client
    2. Authenticates to get a token
    3. Triggers the backup
    4. Cleans up the temporary client
    5. Exits with appropriate status code

    Args:
        backup_type: Type of backup ("full" or "incremental")
        schedule_id: Optional schedule ID that triggered this backup
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
        response = trigger_backup(token, backup_type, schedule_id)

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
    schedule_id = getattr(args, "schedule_id", None)
    create_backup(args.backup_type, schedule_id)


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
    backup_parser.add_argument(
        "--schedule-id",
        type=int,
        required=False,
        help="Schedule ID that triggered this backup",
    )
