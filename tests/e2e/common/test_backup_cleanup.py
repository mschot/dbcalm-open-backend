"""End-to-end tests for backup cleanup functionality."""

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import requests
from utils import wait_for_backup_completion, wait_for_cleanup_completion

# Constants
EXPECTED_BACKUP_COUNT_IN_CHAIN = 2
HTTP_OK = 200
HTTP_ACCEPTED = 202
HTTP_TIMEOUT = 10
BACKUP_DIR = "/var/backups/dbcalm"
DBCALM_DB_PATH = "/var/lib/dbcalm/db.sqlite3"


def create_schedule_via_api(  # noqa: PLR0913
    token: str,
    api_base_url: str,
    backup_type: str = "full",
    frequency: str = "daily",
    hour: int = 3,
    minute: int = 0,
    retention_value: int = 7,
    retention_unit: str = "days",
) -> int:
    """Create a schedule via API.

    Args:
        token: Bearer token
        api_base_url: API base URL
        backup_type: Type of backup (full/incremental)
        frequency: Frequency of backup
        hour: Hour to run backup
        minute: Minute to run backup
        retention_value: Retention value
        retention_unit: Retention unit (days/weeks/months)

    Returns:
        Schedule ID
    """
    response = requests.post(
        f"{api_base_url}/schedules",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "backup_type": backup_type,
            "frequency": frequency,
            "hour": hour,
            "minute": minute,
            "retention_value": retention_value,
            "retention_unit": retention_unit,
            "enabled": True,
        },
        verify=False,  # noqa: S501
        timeout=HTTP_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["id"]


def delete_schedule_via_api(
    token: str,
    api_base_url: str,
    schedule_id: int,
) -> None:
    """Delete a schedule via API.

    Args:
        token: Bearer token
        api_base_url: API base URL
        schedule_id: Schedule ID to delete
    """
    response = requests.delete(
        f"{api_base_url}/schedules/{schedule_id}",
        headers={"Authorization": f"Bearer {token}"},
        verify=False,  # noqa: S501
        timeout=HTTP_TIMEOUT,
    )
    response.raise_for_status()


def create_backup_via_api(
    token: str,
    api_base_url: str,
    backup_type: str = "full",
    from_backup_id: str | None = None,
) -> str:
    """Create a backup via API and wait for completion.

    Args:
        token: Bearer token
        api_base_url: API base URL
        backup_type: Type of backup (full/incremental)
        from_backup_id: Parent backup ID for incremental backups

    Returns:
        Backup ID
    """
    request_data = {"type": backup_type}
    if from_backup_id:
        request_data["from_backup_id"] = from_backup_id

    response = requests.post(
        f"{api_base_url}/backups",
        headers={"Authorization": f"Bearer {token}"},
        json=request_data,
        verify=False,  # noqa: S501
        timeout=HTTP_TIMEOUT,
    )
    response.raise_for_status()
    process_id = response.json()["pid"]

    # Wait for backup to complete
    process_status = wait_for_backup_completion(
        token,
        process_id,
        api_base_url=api_base_url,
    )

    return process_status["resource_id"]


def update_backup_timestamp(
    db_connection: sqlite3.Connection,
    backup_id: str,
    start_time: datetime,
    end_time: datetime,
) -> None:
    """Update backup timestamps directly in database.

    Args:
        db_connection: Database connection
        backup_id: Backup identifier
        start_time: New start time (must be timezone-aware)
        end_time: New end time (must be timezone-aware)
    """
    cursor = db_connection.cursor()
    # Convert datetime to ISO format string for SQLite storage
    # The adapter will handle adding UTC timezone when reading back
    cursor.execute(
        """
        UPDATE backup
        SET start_time = ?, end_time = ?
        WHERE id = ?
        """,
        (start_time.isoformat(), end_time.isoformat(), backup_id),
    )
    db_connection.commit()


def verify_backup_exists(
    db_connection: sqlite3.Connection,
    backup_id: str,
) -> bool:
    """Check if backup exists in both database and filesystem.

    Args:
        db_connection: Database connection
        backup_id: Backup identifier

    Returns:
        True if backup exists in both DB and filesystem, False otherwise
    """
    # Check database
    cursor = db_connection.cursor()
    cursor.execute("SELECT id FROM backup WHERE id = ?", (backup_id,))
    result = cursor.fetchone()
    if not result:
        return False

    # Check filesystem
    backup_path = Path(f"{BACKUP_DIR}/{backup_id}")
    return backup_path.exists()


def verify_backup_deleted(
    db_connection: sqlite3.Connection,
    backup_id: str,
) -> bool:
    """Check if backup is deleted from both database and filesystem.

    Args:
        db_connection: Database connection
        backup_id: Backup identifier

    Returns:
        True if backup is deleted from both DB and filesystem, False otherwise
    """
    # Check database
    cursor = db_connection.cursor()
    cursor.execute("SELECT id FROM backup WHERE id = ?", (backup_id,))
    result = cursor.fetchone()
    if result:
        return False

    # Check filesystem
    backup_path = Path(f"{BACKUP_DIR}/{backup_id}")
    return not backup_path.exists()


def get_dbcalm_db() -> sqlite3.Connection:
    """Create a connection to the dbcalm SQLite database.

    Note: Should be called AFTER backups are created via API to ensure tables exist.
    """
    import time  # noqa: PLC0415

    # Give SQLAlchemy a moment to commit table creation
    time.sleep(0.5)

    conn = sqlite3.connect(DBCALM_DB_PATH)

    # Debug: Check if backup table exists
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",
    )
    tables = cursor.fetchall()
    if not any(t[0] == "backup" for t in tables):
        msg = f"backup table not found in {DBCALM_DB_PATH}. Tables: {tables}"
        raise RuntimeError(msg)

    return conn


class TestBackupCleanup:
    """E2E tests for backup cleanup with retention policies."""

    def test_cleanup_deletes_single_expired_backups(
        self,
        api_token: str,
        api_base_url: str,
    ) -> None:
        """Test that cleanup deletes expired backups while preserving recent ones."""
        # Step 1: Create schedule with 7-day retention via API
        schedule_id = create_schedule_via_api(
            api_token,
            api_base_url,
            backup_type="full",
            frequency="daily",
            hour=3,
            minute=0,
            retention_value=7,
            retention_unit="days",
        )

        # Step 2: Create two full backups via API
        old_backup_id = create_backup_via_api(
            api_token,
            api_base_url,
            backup_type="full",
        )

        recent_backup_id = create_backup_via_api(
            api_token,
            api_base_url,
            backup_type="full",
        )

        # Step 3: Connect to database and associate backups with schedule
        # (Real backups are created without schedule_id, so we update them)
        dbcalm_db = get_dbcalm_db()
        try:
            current_time = datetime.now(tz=UTC)
            cursor = dbcalm_db.cursor()
            cursor.execute(
                "UPDATE backup SET schedule_id = ? WHERE id = ?",
                (schedule_id, old_backup_id),
            )
            cursor.execute(
                "UPDATE backup SET schedule_id = ? WHERE id = ?",
                (schedule_id, recent_backup_id),
            )
            dbcalm_db.commit()

            # Step 4: Manually update old backup to 10 days ago via SQL
            old_time = current_time - timedelta(days=10)
            update_backup_timestamp(
                dbcalm_db,
                backup_id=old_backup_id,
                start_time=old_time,
                end_time=old_time,
            )

            # Step 5: Run cleanup via API
            response = requests.post(
                f"{api_base_url}/cleanup",
                headers={"Authorization": f"Bearer {api_token}"},
                json={"schedule_id": schedule_id},
                verify=False,  # noqa: S501
                timeout=HTTP_TIMEOUT,
            )
            error_msg = f"Failed to start cleanup: {response.text}"
            assert response.status_code == HTTP_ACCEPTED, error_msg
            process_id = response.json()["pid"]

            # Wait for cleanup to complete
            wait_for_cleanup_completion(
                api_token, process_id, api_base_url=api_base_url,
            )

            # Step 6: Verify results
            # Old backup should be deleted
            assert verify_backup_deleted(dbcalm_db, old_backup_id), (
                "Old backup should be deleted from both DB and filesystem"
            )

            # Recent backup should still exist
            assert verify_backup_exists(dbcalm_db, recent_backup_id), (
                "Recent backup should still exist in both DB and filesystem"
            )
        finally:
            # Cleanup: Delete ALL backups for this schedule to prevent
            # interference with other tests
            cursor = dbcalm_db.cursor()
            cursor.execute("DELETE FROM backup WHERE schedule_id = ?", (schedule_id,))
            dbcalm_db.commit()
            dbcalm_db.close()

        # Cleanup: delete the schedule via API
        delete_schedule_via_api(api_token, api_base_url, schedule_id)

    def test_cleanup_respects_backup_chains(
        self,
        api_token: str,
        api_base_url: str,
    ) -> None:
        """Test that cleanup respects backup chains based on retention."""
        # Step 1: Create schedule with 7-day retention via API
        schedule_id = create_schedule_via_api(
            api_token,
            api_base_url,
            backup_type="full",
            frequency="daily",
            hour=3,
            minute=0,
            retention_value=7,
            retention_unit="days",
        )

        # Step 2: Create backup chain (full + incremental) via API
        full_backup_id = create_backup_via_api(
            api_token,
            api_base_url,
            backup_type="full",
        )

        incremental_backup_id = create_backup_via_api(
            api_token,
            api_base_url,
            backup_type="incremental",
            from_backup_id=full_backup_id,
        )

        # Step 3: Connect to database and associate backups with schedule
        dbcalm_db = get_dbcalm_db()
        try:
            current_time = datetime.now(tz=UTC)
            cursor = dbcalm_db.cursor()
            cursor.execute(
                "UPDATE backup SET schedule_id = ? WHERE id = ?",
                (schedule_id, full_backup_id),
            )
            cursor.execute(
                "UPDATE backup SET schedule_id = ? WHERE id = ?",
                (schedule_id, incremental_backup_id),
            )
            dbcalm_db.commit()

            # Part A: Set only full backup to 10 days ago
            # Step 4: Update full backup timestamp via SQL
            old_time = current_time - timedelta(days=10)
            update_backup_timestamp(
                dbcalm_db,
                backup_id=full_backup_id,
                start_time=old_time,
                end_time=old_time,
            )

            # Step 5: Run cleanup via API
            response = requests.post(
                f"{api_base_url}/cleanup",
                headers={"Authorization": f"Bearer {api_token}"},
                json={"schedule_id": schedule_id},
                verify=False,  # noqa: S501
                timeout=HTTP_TIMEOUT,
            )
            error_msg = f"Failed to start cleanup: {response.text}"
            assert response.status_code == HTTP_ACCEPTED, error_msg
            process_id_a = response.json()["pid"]

            # Wait for cleanup to complete
            wait_for_cleanup_completion(
                api_token, process_id_a, api_base_url=api_base_url,
            )

            # Step 6: Verify chain is preserved (incremental is still recent)
            assert verify_backup_exists(dbcalm_db, full_backup_id), (
                "Full backup should be preserved (chain has recent incremental)"
            )
            assert verify_backup_exists(dbcalm_db, incremental_backup_id), (
                "Incremental backup should be preserved"
            )

            # Part B: Set both backups to 10 days ago
            # Step 7: Update incremental backup timestamp via SQL
            update_backup_timestamp(
                dbcalm_db,
                backup_id=incremental_backup_id,
                start_time=old_time,
                end_time=old_time,
            )

            # Step 8: Run cleanup again via API
            response = requests.post(
                f"{api_base_url}/cleanup",
                headers={"Authorization": f"Bearer {api_token}"},
                json={"schedule_id": schedule_id},
                verify=False,  # noqa: S501
                timeout=HTTP_TIMEOUT,
            )
            error_msg = f"Failed to start cleanup: {response.text}"
            assert response.status_code == HTTP_ACCEPTED, error_msg
            process_id_b = response.json()["pid"]

            # Wait for cleanup to complete
            wait_for_cleanup_completion(
                api_token, process_id_b, api_base_url=api_base_url,
            )

            # Step 9: Verify entire chain is deleted
            assert verify_backup_deleted(dbcalm_db, full_backup_id), (
                "Full backup should be deleted (entire chain expired)"
            )
            assert verify_backup_deleted(dbcalm_db, incremental_backup_id), (
                "Incremental backup should be deleted (entire chain expired)"
            )
        finally:
            dbcalm_db.close()

        # Cleanup: delete the schedule via API
        delete_schedule_via_api(api_token, api_base_url, schedule_id)
