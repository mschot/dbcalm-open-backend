"""End-to-end tests for DBCalm backup and restore functionality."""
from pathlib import Path

import pymysql
import requests
from utils import (
    MariaDBService,
    clear_mysql_data_directory,
    create_backup,
    load_sql_file,
    verify_data_integrity,
    verify_row_count,
    wait_for_backup_completion,
    wait_for_restore_completion,
)

# Constants
HTTP_OK = 200
HTTP_ACCEPTED = 202
HTTP_PRECONDITION_FAILED = 412
HTTP_TIMEOUT = 10
MIN_EXPECTED_BACKUPS = 2


class TestFullBackupRestore:
    """Test full backup and restore workflow."""

    def test_full_backup_creation(
        self,
        api_token: str,
        api_base_url: str,
        db_connection: pymysql.Connection,
    ) -> None:
        """Test creating a full backup."""
        # Load initial dataset
        load_sql_file(db_connection, "fixtures/initial_data.sql")
        assert verify_row_count(db_connection, {"users": 5, "orders": 5})

        # Create full backup
        response = requests.post(
            f"{api_base_url}/backups",
            headers={"Authorization": f"Bearer {api_token}"},
            json={"type": "full"},
            verify=False,  # noqa: S501
            timeout=HTTP_TIMEOUT,
        )

        error_msg = f"Failed to create backup: {response.text}"
        assert response.status_code in (HTTP_OK, HTTP_ACCEPTED), error_msg
        backup_data = response.json()
        assert "pid" in backup_data
        process_id = backup_data["pid"]

        # Wait for backup to complete
        process_status = wait_for_backup_completion(
            api_token,
            process_id,
            api_base_url=api_base_url,
        )

        # Get the actual backup ID from the process status
        backup_id = process_status["resource_id"]
        assert backup_id is not None, "Backup ID not found in process status"

        # Verify backup files exist
        backup_dir = Path(f"/var/backups/dbcalm/{backup_id}")
        backup_not_found_msg = f"Backup directory not found: {backup_dir}"
        assert backup_dir.exists(), backup_not_found_msg
        assert list(backup_dir.iterdir()), "Backup directory is empty"

    def test_full_restore(
        self,
        api_token: str,
        api_base_url: str,
        db_connection: pymysql.Connection,
        mariadb_service: type[MariaDBService],
    ) -> None:
        """Test restoring from a full backup."""
        # Load initial dataset and create backup
        load_sql_file(db_connection, "fixtures/initial_data.sql")
        process_id = create_backup(api_token, "full", api_base_url=api_base_url)
        process_status = wait_for_backup_completion(api_token, process_id, api_base_url=api_base_url)
        backup_id = process_status["resource_id"]

        # Add more data after backup
        load_sql_file(db_connection, "fixtures/incremental_data.sql")
        assert verify_row_count(db_connection, {"users": 8, "orders": 7})

        # Close connection before restore
        db_connection.close()

        # Stop MariaDB and clear data directory
        mariadb_service.stop()
        clear_mysql_data_directory()

        # Restore via API
        response = requests.post(
            f"{api_base_url}/restores",
            headers={"Authorization": f"Bearer {api_token}"},
            json={"backup_id": backup_id, "target": "database"},
            verify=False,  # noqa: S501
            timeout=HTTP_TIMEOUT,
        )

        error_msg = f"Failed to start restore: {response.text}"
        assert response.status_code in (HTTP_OK, HTTP_ACCEPTED), error_msg
        process_id = response.json()["pid"]

        # Wait for restore to complete
        process_status = wait_for_restore_completion(
            api_token,
            process_id,
            api_base_url=api_base_url,
        )

        # Start MariaDB
        mariadb_service.start()

        # Reconnect and validate
        new_connection = pymysql.connect(
            host="localhost",
            user="root",
            password="",
            database="testdb",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )

        try:
            # Validate: Only initial data present (not incremental)
            assert verify_row_count(new_connection, {"users": 5, "orders": 5})
            assert verify_data_integrity(new_connection, "initial")
        finally:
            new_connection.close()


class TestIncrementalBackupRestore:
    """Test incremental backup and restore workflow."""

    def test_incremental_backup_creation(
        self,
        api_token: str,
        api_base_url: str,
        db_connection: pymysql.Connection,
    ) -> None:
        """Test creating an incremental backup."""
        # Load initial dataset and create full backup
        load_sql_file(db_connection, "fixtures/initial_data.sql")
        full_process_id = create_backup(api_token, "full", api_base_url=api_base_url)
        full_process_status = wait_for_backup_completion(
            api_token,
            full_process_id,
            api_base_url=api_base_url,
        )
        full_backup_id = full_process_status["resource_id"]

        # Add incremental data
        load_sql_file(db_connection, "fixtures/incremental_data.sql")
        assert verify_row_count(db_connection, {"users": 8, "orders": 7})

        # Create incremental backup
        response = requests.post(
            f"{api_base_url}/backups",
            headers={"Authorization": f"Bearer {api_token}"},
            json={"type": "incremental", "from_backup_id": full_backup_id},
            verify=False,  # noqa: S501
            timeout=HTTP_TIMEOUT,
        )

        error_msg = f"Failed to create incremental backup: {response.text}"
        assert response.status_code in (HTTP_OK, HTTP_ACCEPTED), error_msg
        process_id = response.json()["pid"]

        # Wait for backup to complete
        process_status = wait_for_backup_completion(
            api_token,
            process_id,
            api_base_url=api_base_url,
        )
        incremental_backup_id = process_status["resource_id"]

        # Verify backup files exist
        backup_dir = Path(f"/var/backups/dbcalm/{incremental_backup_id}")
        backup_not_found_msg = f"Incremental backup directory not found: {backup_dir}"
        assert backup_dir.exists(), backup_not_found_msg

    def test_incremental_restore(
        self,
        api_token: str,
        api_base_url: str,
        db_connection: pymysql.Connection,
        mariadb_service: type[MariaDBService],
    ) -> None:
        """Test restoring from incremental backup (includes full backup chain)."""
        # Load initial dataset and create full backup
        load_sql_file(db_connection, "fixtures/initial_data.sql")
        full_process_id = create_backup(api_token, "full", api_base_url=api_base_url)
        full_process_status = wait_for_backup_completion(
            api_token,
            full_process_id,
            api_base_url=api_base_url,
        )
        full_backup_id = full_process_status["resource_id"]

        # Add incremental data and create incremental backup
        load_sql_file(db_connection, "fixtures/incremental_data.sql")
        incr_process_id = create_backup(
            api_token,
            "incremental",
            from_backup_id=full_backup_id,
            api_base_url=api_base_url,
        )
        incr_process_status = wait_for_backup_completion(
            api_token,
            incr_process_id,
            api_base_url=api_base_url,
        )
        incremental_backup_id = incr_process_status["resource_id"]

        # Close connection before restore
        db_connection.close()

        # Stop MariaDB and clear data directory
        mariadb_service.stop()
        clear_mysql_data_directory()

        # Restore incremental backup (should restore full + incremental)
        response = requests.post(
            f"{api_base_url}/restores",
            headers={"Authorization": f"Bearer {api_token}"},
            json={"backup_id": incremental_backup_id, "target": "database"},
            verify=False,  # noqa: S501
            timeout=HTTP_TIMEOUT,
        )

        error_msg = f"Failed to start restore: {response.text}"
        assert response.status_code in (HTTP_OK, HTTP_ACCEPTED), error_msg
        process_id = response.json()["pid"]

        # Wait for restore to complete
        process_status = wait_for_restore_completion(
            api_token,
            process_id,
            api_base_url=api_base_url,
        )

        # Start MariaDB
        mariadb_service.start()

        # Reconnect and validate
        new_connection = pymysql.connect(
            host="localhost",
            user="root",
            password="",
            database="testdb",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )

        try:
            # Validate: All data present (initial + incremental)
            assert verify_row_count(new_connection, {"users": 8, "orders": 7})
            assert verify_data_integrity(new_connection, "full")
        finally:
            new_connection.close()


class TestCredentialsValidation:
    """Test credentials file validation."""

    def test_backup_requires_credentials_file(
        self,
        api_token: str,
        api_base_url: str,
    ) -> None:
        """Test that backup fails when credentials file is missing."""
        # Remove credentials file
        credentials_file = Path("/etc/dbcalm/credentials.cnf")
        original_content = None

        if credentials_file.exists():
            original_content = credentials_file.read_text()
            credentials_file.unlink()

        try:
            # Attempt backup - should fail with 412
            response = requests.post(
                f"{api_base_url}/backups",
                headers={"Authorization": f"Bearer {api_token}"},
                json={"type": "full"},
                verify=False,  # noqa: S501
                timeout=HTTP_TIMEOUT,
            )

            error_msg = f"Expected 412, got {response.status_code}"
            assert response.status_code == HTTP_PRECONDITION_FAILED, error_msg
            assert "credentials" in response.json()["detail"].lower()

        finally:
            # Restore credentials file
            if original_content:
                credentials_file.write_text(original_content)

    def test_backup_requires_client_dbcalm_section(
        self,
        api_token: str,
        api_base_url: str,
    ) -> None:
        """Test that backup fails when [client-dbcalm] section is missing."""
        credentials_file = Path("/etc/dbcalm/credentials.cnf")
        original_content = credentials_file.read_text()

        # Write credentials file without [client-dbcalm] section
        credentials_file.write_text("[client]\nuser=test\npassword=test\n")

        try:
            # Attempt backup - should fail with 412
            response = requests.post(
                f"{api_base_url}/backups",
                headers={"Authorization": f"Bearer {api_token}"},
                json={"type": "full"},
                verify=False,  # noqa: S501
                timeout=HTTP_TIMEOUT,
            )

            error_msg = f"Expected 412, got {response.status_code}"
            assert response.status_code == HTTP_PRECONDITION_FAILED, error_msg
            assert "client-dbcalm" in response.json()["detail"].lower()

        finally:
            # Restore original credentials
            credentials_file.write_text(original_content)


class TestRestorePreconditions:
    """Test restore precondition validations."""

    def test_restore_requires_server_stopped(
        self,
        api_token: str,
        api_base_url: str,
        db_connection: pymysql.Connection,
        mariadb_service: type[MariaDBService],
    ) -> None:
        """Test that database restore fails when MariaDB is running."""
        # Create a backup to restore from
        load_sql_file(db_connection, "fixtures/initial_data.sql")
        process_id = create_backup(api_token, "full", api_base_url=api_base_url)
        process_status = wait_for_backup_completion(api_token, process_id, api_base_url=api_base_url)
        backup_id = process_status["resource_id"]

        # Ensure MariaDB is running
        mariadb_service.ensure_running()

        # Attempt restore - should fail with 412
        response = requests.post(
            f"{api_base_url}/restores",
            headers={"Authorization": f"Bearer {api_token}"},
            json={"backup_id": backup_id, "target": "database"},
            verify=False,  # noqa: S501
            timeout=HTTP_TIMEOUT,
        )

        error_msg = f"Expected 412, got {response.status_code}"
        assert response.status_code == HTTP_PRECONDITION_FAILED, error_msg
        assert "server" in response.json()["detail"].lower()
        assert "stopped" in response.json()["detail"].lower()

    def test_restore_requires_empty_data_directory(
        self,
        api_token: str,
        api_base_url: str,
        db_connection: pymysql.Connection,
        mariadb_service: type[MariaDBService],
    ) -> None:
        """Test that restore fails when data directory is not empty."""
        # Create a backup to restore from
        load_sql_file(db_connection, "fixtures/initial_data.sql")
        process_id = create_backup(api_token, "full", api_base_url=api_base_url)
        process_status = wait_for_backup_completion(api_token, process_id, api_base_url=api_base_url)
        backup_id = process_status["resource_id"]

        # Close connection and stop MariaDB (but don't clear data directory)
        db_connection.close()
        mariadb_service.stop()

        # Attempt restore - should fail with 412
        response = requests.post(
            f"{api_base_url}/restores",
            headers={"Authorization": f"Bearer {api_token}"},
            json={"backup_id": backup_id, "target": "database"},
            verify=False,  # noqa: S501
            timeout=HTTP_TIMEOUT,
        )

        # Restart MariaDB for cleanup
        mariadb_service.start()

        error_msg = f"Expected 412, got {response.status_code}"
        assert response.status_code == HTTP_PRECONDITION_FAILED, error_msg
        assert "data directory" in response.json()["detail"].lower()
        assert "empty" in response.json()["detail"].lower()


class TestBackupListing:
    """Test backup listing and retrieval."""

    def test_list_backups(
        self,
        api_token: str,
        api_base_url: str,
        db_connection: pymysql.Connection,
    ) -> None:
        """Test listing backups via API."""
        # Create multiple backups
        load_sql_file(db_connection, "fixtures/initial_data.sql")

        backup_ids = []
        for _ in range(2):
            process_id = create_backup(api_token, "full", api_base_url=api_base_url)
            process_status = wait_for_backup_completion(
                api_token,
                process_id,
                api_base_url=api_base_url,
            )
            backup_ids.append(process_status["resource_id"])

        # List backups
        response = requests.get(
            f"{api_base_url}/backups",
            headers={"Authorization": f"Bearer {api_token}"},
            verify=False,  # noqa: S501
            timeout=HTTP_TIMEOUT,
        )

        assert response.status_code == HTTP_OK
        backups = response.json()

        # Verify our backups are in the list
        backup_ids_in_response = [b["id"] for b in backups if b["id"] in backup_ids]
        assert len(backup_ids_in_response) >= MIN_EXPECTED_BACKUPS

    def test_get_backup_details(
        self,
        api_token: str,
        api_base_url: str,
        db_connection: pymysql.Connection,
    ) -> None:
        """Test retrieving specific backup details."""
        # Create a backup
        load_sql_file(db_connection, "fixtures/initial_data.sql")
        process_id = create_backup(api_token, "full", api_base_url=api_base_url)
        process_status = wait_for_backup_completion(api_token, process_id, api_base_url=api_base_url)
        backup_id = process_status["resource_id"]

        # Get backup details
        response = requests.get(
            f"{api_base_url}/backups/{backup_id}",
            headers={"Authorization": f"Bearer {api_token}"},
            verify=False,  # noqa: S501
            timeout=HTTP_TIMEOUT,
        )

        assert response.status_code == HTTP_OK
        backup = response.json()
        assert backup["id"] == backup_id
        assert backup["backup_type"] == "full"
