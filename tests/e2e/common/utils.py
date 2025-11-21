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
    """Clear MySQL data directory preserving only runtime socket/pid files."""
    data_dir = Path("/var/lib/mysql")
    if not data_dir.exists():
        return

    # Only preserve runtime files (socket and pid)
    preserve_extensions = {".sock", ".pid"}

    # Remove all files and directories except runtime files
    for item in data_dir.iterdir():
        if item.suffix in preserve_extensions:
            continue

        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        except Exception as e:
            print(f"Warning: Failed to remove {item}: {e}")

    # Verify directory is empty (except runtime files)
    remaining = [
        f.name for f in data_dir.iterdir()
        if f.suffix not in preserve_extensions
    ]
    if remaining:
        error_msg = (
            f"Data directory /var/lib/mysql is not empty after clearing. "
            f"Remaining files: {remaining}"
        )
        raise RuntimeError(error_msg)


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
        print(f"DEBUG: Restore status check - Full response: {process_status}")
        print(f"DEBUG: Status value: {status}")

        if status == "success":
            # Restore completed successfully
            print(f"DEBUG: Restore succeeded! Final status: {process_status}")
            return process_status
        if status == "failed":
            error_msg = f"Restore process failed: {process_status.get('error')}"
            print(f"DEBUG: Restore failed! Status: {process_status}")
            raise RuntimeError(error_msg)

        time.sleep(BACKUP_POLL_INTERVAL)

    timeout_msg = f"Restore process {process_id} did not complete within {timeout}s"
    raise TimeoutError(timeout_msg)


def wait_for_cleanup_completion(
    token: str,
    process_id: int,
    timeout: int = 60,
    api_base_url: str = "https://localhost:8335",
) -> dict[str, Any]:
    """Wait for a cleanup process to complete by polling its status.

    Args:
        token: Bearer token for API authentication
        process_id: Process ID from the HTTP 202 response
        timeout: Maximum time to wait in seconds (default 60)
        api_base_url: Base URL for API

    Returns:
        Final process status dict with cleanup information

    Raises:
        TimeoutError: If cleanup doesn't complete within timeout
        RuntimeError: If cleanup fails
    """
    headers = {"Authorization": f"Bearer {token}"}
    start_time = time.time()

    while time.time() - start_time < timeout:
        # Poll the status endpoint
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
            # Cleanup completed successfully
            return process_status
        if status == "failed":
            error_msg = (
                f"Cleanup process failed. "
                f"Full status: {process_status}"
            )
            raise RuntimeError(error_msg)

        time.sleep(BACKUP_POLL_INTERVAL)

    # Include final status in timeout error for debugging
    timeout_msg = (
        f"Cleanup process {process_id} did not complete within {timeout}s. "
        f"Last status: {process_status}"
    )
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
        # Create log file with correct ownership
        log_file = Path("/var/log/db-restart.log")
        log_file.touch(exist_ok=True)
        subprocess.run(
            ["chown", "mysql:mysql", str(log_file)],
            check=False,
        )
        subprocess.run(
            ["chmod", "664", str(log_file)],
            check=False,
        )

        # Start MariaDB in background
        cmd = ["mysqld_safe", "--log-error=/var/log/db-restart.log"]
        print(f"DEBUG: Starting MariaDB with command: {' '.join(cmd)}")

        # Capture output to log files instead of discarding
        with (
            Path("/var/log/db-restart-stdout.log").open("w") as stdout_log,
            Path("/var/log/db-restart-stderr.log").open("w") as stderr_log,
        ):
            process = subprocess.Popen(
                cmd,
                stdout=stdout_log,
                stderr=stderr_log,
            )

        print(f"DEBUG: MariaDB process started with PID: {process.pid}")
        time.sleep(MARIADB_START_WAIT)

        # Check if process is still alive
        poll_result = process.poll()
        if poll_result is not None:
            print(
                "ERROR: MariaDB process died immediately with "
                f"exit code {poll_result}",
            )
            print("DEBUG: Contents of /var/log/db-restart.log:")
            try:
                with Path("/var/log/db-restart.log").open() as f:
                    print(f.read())
            except Exception as e:
                print(f"Could not read log file: {e}")
            msg = f"MariaDB process died immediately with exit code {poll_result}"
            raise RuntimeError(msg)

        print("DEBUG: MariaDB process is still running, waiting for it to be ready...")

        # Wait for MariaDB to be ready (up to 30 seconds)
        for i in range(30):
            if MariaDBService.is_running():
                print(f"DEBUG: MariaDB is ready after {i+1} seconds!")
                return

            # Check if process died during wait
            poll_result = process.poll()
            if poll_result is not None:
                print(f"ERROR: MariaDB process died with exit code {poll_result}")
                print("DEBUG: Contents of /var/log/db-restart.log:")
                try:
                    with Path("/var/log/db-restart.log").open() as f:
                        print(f.read())
                except Exception as e:
                    print(f"Could not read log file: {e}")
                msg = f"MariaDB process died with exit code {poll_result}"
                raise RuntimeError(msg)

            time.sleep(1)

        # Timeout reached - print logs to help diagnose
        print("ERROR: MariaDB failed to become ready within 30 seconds")
        print("DEBUG: Contents of /var/log/db-restart.log:")
        try:
            with Path("/var/log/db-restart.log").open() as f:
                print(f.read())
        except Exception as e:
            print(f"Could not read log file: {e}")

        msg = "Failed to start MariaDB within 30 seconds"
        raise RuntimeError(msg)

    @staticmethod
    def stop() -> None:
        """Stop MariaDB service."""
        subprocess.run(
            ["mysqladmin", "-u", "root", "shutdown"],
            check=False,
        )
        time.sleep(MYSQL_SHUTDOWN_WAIT)

    @staticmethod
    def is_running() -> bool:
        """Check if MariaDB service is running."""
        result = subprocess.run(
            ["mysqladmin", "ping", "-h", "localhost", "--silent"],
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


class MySQLService:
    """Helper class to manage MySQL service (without systemd)."""

    @staticmethod
    def start() -> None:  # noqa: C901, PLR0915
        """Start MySQL service."""
        # Debug: Check data directory ownership before starting
        print("DEBUG: Checking /var/lib/mysql ownership before starting MySQL...")
        result = subprocess.run(
            ["ls", "-la", "/var/lib/mysql"],
            capture_output=True,
            text=True,
            check=False,
        )
        print(result.stdout)

        # Fix ownership of data directory (needed after restore operations)
        # XtraBackup restores files as root, but MySQL needs them owned by mysql user
        print("DEBUG: Fixing ownership of /var/lib/mysql...")
        subprocess.run(
            ["chown", "-R", "mysql:mysql", "/var/lib/mysql"],
            check=False,
        )

        # Create log file with correct ownership
        log_file = Path("/var/log/db-restart.log")
        log_file.touch(exist_ok=True)
        subprocess.run(
            ["chown", "mysql:mysql", str(log_file)],
            check=False,
        )
        subprocess.run(
            ["chmod", "664", str(log_file)],
            check=False,
        )

        # Start MySQL in background
        # MySQL 8.x uses mysqld directly (no mysqld_safe)
        # Note: MySQL 8.x requires --user=mysql flag when running as root
        cmd = ["mysqld", "--user=mysql", "--log-error=/var/log/db-restart.log"]
        print(f"DEBUG: Starting MySQL with command: {' '.join(cmd)}")

        # Capture output to log files instead of discarding
        with (
            Path("/var/log/db-restart-stdout.log").open("w") as stdout_log,
            Path("/var/log/db-restart-stderr.log").open("w") as stderr_log,
        ):
            process = subprocess.Popen(
                cmd,
                stdout=stdout_log,
                stderr=stderr_log,
            )

        print(f"DEBUG: MySQL process started with PID: {process.pid}")
        time.sleep(MARIADB_START_WAIT)

        # Check if process is still alive
        poll_result = process.poll()
        if poll_result is not None:
            print(f"ERROR: MySQL process died immediately with exit code {poll_result}")

            # Try to read all possible log files
            print("DEBUG: Contents of /var/log/db-restart.log:")
            try:
                with Path("/var/log/db-restart.log").open() as f:
                    print(f.read())
            except Exception as e:
                print(f"Could not read db-restart.log: {e}")

            print("DEBUG: Contents of /var/log/db-restart-stdout.log:")
            try:
                with Path("/var/log/db-restart-stdout.log").open() as f:
                    content = f.read()
                    print(content if content else "(empty)")
            except Exception as e:
                print(f"Could not read db-restart-stdout.log: {e}")

            print("DEBUG: Contents of /var/log/db-restart-stderr.log:")
            try:
                with Path("/var/log/db-restart-stderr.log").open() as f:
                    content = f.read()
                    print(content if content else "(empty)")
            except Exception as e:
                print(f"Could not read db-restart-stderr.log: {e}")

            # Check if /var/log directory exists and is writable
            print("DEBUG: Checking /var/log directory:")
            result = subprocess.run(
                ["ls", "-la", "/var/log/"],
                capture_output=True,
                text=True,
                check=False,
            )
            print(result.stdout)

            msg = (
                f"MySQL process died immediately with exit code {poll_result}"
            )
            raise RuntimeError(msg)

        print("DEBUG: MySQL process is still running, waiting for it to be ready...")

        # Wait for MySQL to be ready (up to 30 seconds)
        for i in range(30):
            if MySQLService.is_running():
                print(f"DEBUG: MySQL is ready after {i+1} seconds!")
                return

            # Check if process died during wait
            poll_result = process.poll()
            if poll_result is not None:
                print(
                    f"ERROR: MySQL process died with exit code {poll_result}",
                )

                # Try to read all log files
                log_files = [
                    "db-restart.log",
                    "db-restart-stdout.log",
                    "db-restart-stderr.log",
                ]
                for log_file in log_files:
                    print(f"DEBUG: Contents of /var/log/{log_file}:")
                    try:
                        with Path(f"/var/log/{log_file}").open() as f:
                            content = f.read()
                            print(content if content else "(empty)")
                    except Exception as e:
                        print(f"Could not read {log_file}: {e}")

                msg = f"MySQL process died with exit code {poll_result}"
                raise RuntimeError(msg)

            time.sleep(1)

        # Timeout reached - print logs to help diagnose
        print("ERROR: MySQL failed to become ready within 30 seconds")

        # Try to read all log files
        log_files = [
            "db-restart.log",
            "db-restart-stdout.log",
            "db-restart-stderr.log",
        ]
        for log_file in log_files:
            print(f"DEBUG: Contents of /var/log/{log_file}:")
            try:
                with Path(f"/var/log/{log_file}").open() as f:
                    content = f.read()
                    print(content if content else "(empty)")
            except Exception as e:
                print(f"Could not read {log_file}: {e}")

        msg = "Failed to start MySQL within 30 seconds"
        raise RuntimeError(msg)

    @staticmethod
    def stop() -> None:
        """Stop MySQL service."""
        subprocess.run(
            ["mysqladmin", "-u", "root", "shutdown"],
            check=False,
        )
        time.sleep(MYSQL_SHUTDOWN_WAIT)

    @staticmethod
    def is_running() -> bool:
        """Check if MySQL service is running."""
        result = subprocess.run(
            ["mysqladmin", "ping", "-h", "localhost", "--silent"],
            check=False,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    @staticmethod
    def ensure_running() -> None:
        """Ensure MySQL is running."""
        # MySQL should always be running in the container
        # This is mainly for test compatibility
        if not MySQLService.is_running():
            print("WARNING: MySQL is not running!")
            time.sleep(MARIADB_STATUS_CHECK_WAIT)


def get_database_service() -> type[MariaDBService] | type[MySQLService]:
    """Get appropriate database service based on DB_TYPE environment variable.

    Returns:
        MariaDBService or MySQLService class based on DB_TYPE env var
    """
    import os  # noqa: PLC0415

    db_type = os.getenv("DB_TYPE", "mariadb")

    if db_type == "mysql":
        return MySQLService
    return MariaDBService
