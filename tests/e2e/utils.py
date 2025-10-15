"""Utility functions for E2E tests."""
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

import pymysql
import requests

# Constants
HTTP_TIMEOUT = 10
BACKUP_POLL_INTERVAL = 2
DEFAULT_BACKUP_TIMEOUT = 300
MYSQL_SHUTDOWN_WAIT = 2
MARIADB_START_WAIT = 1
MARIADB_STATUS_CHECK_WAIT = 2
EXPECTED_INCREMENTAL_USER_COUNT = 3


def load_sql_file(connection: pymysql.Connection, sql_file: str) -> None:
    """Load and execute SQL from a file.

    Args:
        connection: PyMySQL connection object
        sql_file: Path to SQL file relative to tests/e2e/
    """
    sql_path = Path("/tests") / sql_file
    with sql_path.open() as f:
        sql_content = f.read()

    # Split by semicolon and execute each statement
    statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]

    with connection.cursor() as cursor:
        for statement in statements:
            if statement:
                cursor.execute(statement)
    connection.commit()


def verify_row_count(
    connection: pymysql.Connection,
    expected_counts: dict[str, int],
) -> bool:
    """Verify row counts in tables match expected values.

    Args:
        connection: PyMySQL connection object
        expected_counts: Dict mapping table names to expected row counts

    Returns:
        True if all counts match, False otherwise
    """
    with connection.cursor() as cursor:
        for table, expected_count in expected_counts.items():
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")  # noqa: S608
            result = cursor.fetchone()
            actual_count = result["count"]
            if actual_count != expected_count:
                msg = (
                    f"Row count mismatch in {table}: "
                    f"expected {expected_count}, got {actual_count}"
                )
                print(msg)
                return False
    return True


def verify_data_integrity(connection: pymysql.Connection, dataset: str) -> bool:
    """Verify data integrity for a specific dataset.

    Args:
        connection: PyMySQL connection object
        dataset: Either "initial" or "full" to check different datasets

    Returns:
        True if data integrity checks pass
    """
    with connection.cursor(pymysql.cursors.DictCursor) as cursor:
        # Check foreign key relationships
        cursor.execute("""
            SELECT o.id, o.user_id, u.id as user_exists
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.id
        """)
        orders = cursor.fetchall()

        for order in orders:
            if order["user_exists"] is None:
                msg = (
                    f"Foreign key violation: order {order['id']} "
                    f"references non-existent user {order['user_id']}"
                )
                print(msg)
                return False

        # Dataset-specific checks
        if dataset == "initial":
            # Check we have exactly the initial users
            cursor.execute("SELECT username FROM users ORDER BY id")
            usernames = [row["username"] for row in cursor.fetchall()]
            expected = ["alice", "bob", "charlie", "diana", "eve"]
            if usernames != expected:
                msg = f"Initial dataset mismatch. Expected {expected}, got {usernames}"
                print(msg)
                return False

        elif dataset == "full":
            # Check we have all users including incremental
            query = (
                "SELECT COUNT(*) as count FROM users "
                "WHERE username IN ('frank', 'grace', 'henry')"
            )
            cursor.execute(query)
            if cursor.fetchone()["count"] != EXPECTED_INCREMENTAL_USER_COUNT:
                print("Incremental users not found in full dataset")
                return False

            # Check updated email
            cursor.execute("SELECT email FROM users WHERE id = 3")
            email = cursor.fetchone()["email"]
            if email != "charlie.updated@example.com":
                print(f"Expected updated email for charlie, got {email}")
                return False

    return True


def clear_mysql_data_directory() -> None:
    """Clear MySQL data directory preserving system files."""
    data_dir = Path("/var/lib/mysql")
    if not data_dir.exists():
        return

    # Files to preserve
    preserve = {
        "ib_buffer_pool",
        "ibdata1",
        "ib_logfile0",
        "ib_logfile1",
    }
    preserve_extensions = {".sock", ".pid", ".err", ".cnf", ".flag"}

    for item in data_dir.iterdir():
        if item.name in preserve or item.suffix in preserve_extensions:
            continue

        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def wait_for_backup_completion(
    token: str,
    process_id: str,
    timeout: int = DEFAULT_BACKUP_TIMEOUT,
    api_base_url: str = "https://localhost:8335",
) -> dict[str, Any]:
    """Wait for a backup process to complete by polling its status.

    Args:
        token: Bearer token for API authentication
        process_id: Process ID (UUID) from the HTTP 202 response
        timeout: Maximum time to wait in seconds
        api_base_url: Base URL for API

    Returns:
        Final process status dict with backup information

    Raises:
        TimeoutError: If backup doesn't complete within timeout
        RuntimeError: If backup fails
    """
    headers = {"Authorization": f"Bearer {token}"}
    start_time = time.time()

    while time.time() - start_time < timeout:
        # Poll the status endpoint, not the backup endpoint
        response = requests.get(
            f"{api_base_url}/status/{process_id}",
            headers=headers,
            verify=False,  # noqa: S501
            timeout=HTTP_TIMEOUT,
        )
        response.raise_for_status()
        process_status = response.json()

        status = process_status.get("status")
        if status == "success":
            # Backup completed successfully
            return process_status
        if status == "failed":
            error_msg = f"Backup process failed: {process_status.get('error')}"
            raise RuntimeError(error_msg)

        time.sleep(BACKUP_POLL_INTERVAL)

    timeout_msg = f"Backup process {process_id} did not complete within {timeout}s"
    raise TimeoutError(timeout_msg)


def wait_for_restore_completion(
    token: str,
    process_id: str,
    timeout: int = DEFAULT_BACKUP_TIMEOUT,
    api_base_url: str = "https://localhost:8335",
) -> dict[str, Any]:
    """Wait for a restore process to complete by polling its status.

    Args:
        token: Bearer token for API authentication
        process_id: Process ID (UUID) from the HTTP 202 response
        timeout: Maximum time to wait in seconds
        api_base_url: Base URL for API

    Returns:
        Final process status dict with restore information

    Raises:
        TimeoutError: If restore doesn't complete within timeout
        RuntimeError: If restore fails
    """
    headers = {"Authorization": f"Bearer {token}"}
    start_time = time.time()

    while time.time() - start_time < timeout:
        # Poll the status endpoint, not the restore endpoint
        response = requests.get(
            f"{api_base_url}/status/{process_id}",
            headers=headers,
            verify=False,  # noqa: S501
            timeout=HTTP_TIMEOUT,
        )
        response.raise_for_status()
        process_status = response.json()

        status = process_status.get("status")
        if status == "success":
            # Restore completed successfully
            return process_status
        if status == "failed":
            error_msg = f"Restore process failed: {process_status.get('error')}"
            raise RuntimeError(error_msg)

        time.sleep(BACKUP_POLL_INTERVAL)

    timeout_msg = f"Restore process {process_id} did not complete within {timeout}s"
    raise TimeoutError(timeout_msg)


def create_backup(
    token: str,
    backup_type: str,
    from_backup_id: str | None = None,
    api_base_url: str = "https://localhost:8335",
) -> str:
    """Create a backup and return its ID.

    Args:
        token: Bearer token for API authentication
        backup_type: "full" or "incremental"
        from_backup_id: Base backup ID for incremental backups
        api_base_url: Base URL for API

    Returns:
        Backup ID
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {"type": backup_type}

    if backup_type == "incremental" and from_backup_id:
        payload["from_backup_id"] = from_backup_id

    response = requests.post(
        f"{api_base_url}/backups",
        headers=headers,
        json=payload,
        verify=False,  # noqa: S501
        timeout=HTTP_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["pid"]


class MariaDBService:
    """Helper class to manage MariaDB service (without systemd)."""

    @staticmethod
    def start() -> None:
        """Start MariaDB service."""
        # MariaDB is already running in the container, this is a no-op
        # but we keep it for compatibility
        time.sleep(MARIADB_START_WAIT)

    @staticmethod
    def stop() -> None:
        """Stop MariaDB service."""
        subprocess.run(
            ["mysqladmin", "-u", "root", "shutdown"],  # noqa: S607
            check=False,
        )
        time.sleep(MYSQL_SHUTDOWN_WAIT)

    @staticmethod
    def is_running() -> bool:
        """Check if MariaDB service is running."""
        result = subprocess.run(
            ["mysqladmin", "ping", "-h", "localhost", "--silent"],  # noqa: S607
            check=False,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    @staticmethod
    def ensure_running() -> None:
        """Ensure MariaDB is running."""
        # MariaDB should always be running in the container
        # This is mainly for test compatibility
        if not MariaDBService.is_running():
            print("WARNING: MariaDB is not running!")
            time.sleep(MARIADB_STATUS_CHECK_WAIT)
