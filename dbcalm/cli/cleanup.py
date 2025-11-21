import argparse
import sys

import requests

from dbcalm.cli.api_client_helper import (
    APIError,
    cleanup_temp_client,
    get_api_url,
    get_bearer_token,
    get_or_create_temp_client,
    wait_for_process_completion,
)


def trigger_cleanup(
    token: str,
    schedule_id: int | None = None,
) -> dict:
    """Call the cleanup API endpoint.

    Args:
        token: Bearer token for authentication
        schedule_id: Optional schedule ID to clean up

    Returns:
        Response JSON from the API

    Raises:
        APIError: If cleanup request fails
    """
    api_url = get_api_url()
    cleanup_url = f"{api_url}/cleanup"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    data = {}
    if schedule_id is not None:
        data["schedule_id"] = schedule_id

    try:
        response = requests.post(
            cleanup_url,
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
        msg = f"Cleanup request failed: {error_msg}"
        raise APIError(msg) from e
    except requests.exceptions.RequestException as e:
        msg = f"Cleanup request failed: {e!s}"
        raise APIError(msg) from e


def run_cleanup(
    schedule_id: int | None = None,
) -> None:
    """Run backup cleanup using the API.

    This function:
    1. Creates a temporary client
    2. Authenticates to get a token
    3. Triggers the cleanup
    4. Waits for completion
    5. Cleans up the temporary client
    6. Exits with appropriate status code

    Args:
        schedule_id: Optional specific schedule ID to clean up
    """
    client_id = None

    try:
        # Step 1: Create temporary client
        client_id, client_secret = get_or_create_temp_client()

        # Step 2: Authenticate
        token = get_bearer_token(client_id, client_secret)

        # Step 3: Trigger cleanup
        response = trigger_cleanup(token, schedule_id)
        process_id = response.get("pid")

        if schedule_id is not None:
            msg = f"Cleanup started for schedule {schedule_id}"
            print(f"{msg} (PID: {process_id})")
        else:
            msg = "Cleanup started for all schedules"
            print(f"{msg} (PID: {process_id})")

        # Step 4: Wait for completion
        print("Waiting for cleanup to complete...")
        final_status = wait_for_process_completion(token, process_id)

        # Step 5: Cleanup
        cleanup_temp_client(client_id)

        # Step 6: Display results and exit
        output = final_status.get("output", "")
        print(f"Success: {output}")
        sys.exit(0)

    except Exception as e:
        # Cleanup on error
        if client_id:
            cleanup_temp_client(client_id)

        print(f"Error: {e!s}")
        sys.exit(1)


def run(args: argparse.Namespace) -> None:
    """Handle cleanup command execution.

    Args:
        args: Parsed command line arguments
    """
    schedule_id = getattr(args, "schedule_id", None)
    run_cleanup(schedule_id)


def configure_parser(subparsers: argparse._SubParsersAction) -> None:
    """Configure the cleanup subcommand parser.

    Args:
        subparsers: Subparser action from main argument parser
    """
    cleanup_parser = subparsers.add_parser(
        "cleanup",
        help="Clean up old backups based on schedule retention policies",
    )
    cleanup_parser.add_argument(
        "--schedule-id",
        type=int,
        required=False,
        help="Specific schedule ID to clean up (cleans all schedules if not specified)",
    )
