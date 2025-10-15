"""Pytest configuration and fixtures for E2E tests."""
import os
import time
from collections.abc import Generator
from pathlib import Path

import pymysql
import pytest
import requests
import urllib3
from utils import MariaDBService

# Constants
HTTP_OK = 200
API_TOKEN_TIMEOUT = 10
CREDENTIALS_FILE_PATH = "/tmp/e2e_credentials.env"  # noqa: S108

# Disable SSL warnings for self-signed certificates in tests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@pytest.fixture(scope="session")
def client_credentials() -> tuple[str, str]:
    """Load API client credentials from environment."""
    client_id = os.getenv("E2E_CLIENT_ID")
    client_secret = os.getenv("E2E_CLIENT_SECRET")

    if not client_id or not client_secret:
        # Try loading from file
        credentials_file = Path(CREDENTIALS_FILE_PATH)
        if credentials_file.exists():
            content = credentials_file.read_text()
            for line in content.strip().split("\n"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    if key == "E2E_CLIENT_ID":
                        client_id = value
                    elif key == "E2E_CLIENT_SECRET":
                        client_secret = value

    if not client_id or not client_secret:
        pytest.fail("API client credentials not found in environment or file")

    return client_id, client_secret


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """Get API base URL from environment."""
    return os.getenv("API_BASE_URL", "https://localhost:8335")


@pytest.fixture(scope="session")
def api_token(
    client_credentials: tuple[str, str],
    api_base_url: str,
) -> str:
    """Get bearer token using client credentials."""
    client_id, client_secret = client_credentials

    response = requests.post(
        f"{api_base_url}/auth/token",
        json={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        verify=False,  # noqa: S501
        timeout=API_TOKEN_TIMEOUT,
    )

    if response.status_code != HTTP_OK:
        error_msg = (
            f"Failed to get API token: "
            f"{response.status_code} - {response.text}"
        )
        pytest.fail(error_msg)

    return response.json()["access_token"]


@pytest.fixture
def db_connection() -> Generator[pymysql.Connection, None, None]:
    """Create a database connection for testing."""
    # Ensure MariaDB is running
    MariaDBService.ensure_running()

    connection = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="testdb",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )

    yield connection

    connection.close()


@pytest.fixture
def mariadb_service() -> type[MariaDBService]:
    """Provide MariaDB service management."""
    return MariaDBService


@pytest.fixture(autouse=True)
def ensure_clean_state(
    db_connection: pymysql.Connection,
) -> Generator[None, None, None]:
    """Ensure database is in clean state before each test."""
    with db_connection.cursor() as cursor:
        # Disable foreign key checks temporarily
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

        # Truncate tables
        cursor.execute("TRUNCATE TABLE orders")
        cursor.execute("TRUNCATE TABLE users")

        # Re-enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

    db_connection.commit()

    yield

    # Add delay between tests to prevent backup directory timestamp collisions
    time.sleep(2)

    # Cleanup after test
    with db_connection.cursor() as cursor:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("TRUNCATE TABLE orders")
        cursor.execute("TRUNCATE TABLE users")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    db_connection.commit()
