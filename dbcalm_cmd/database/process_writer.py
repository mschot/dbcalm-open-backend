"""Minimal database writer for Process records using raw sqlite3.

This module provides a lightweight alternative to SQLAlchemy for command services
that only need to write Process records to the database.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


class ProcessWriter:
    """Lightweight database writer for Process table.

    Uses raw sqlite3 instead of SQLAlchemy to minimize memory footprint.
    Only supports writing/updating Process records - no complex queries.
    """

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize process writer.

        Args:
            db_path: Path to SQLite database file.
                Defaults to /var/lib/dbcalm/db.sqlite3
        """
        if db_path is None:
            db_path = "/var/lib/dbcalm/db.sqlite3"

        self.db_path = db_path
        self._ensure_database_exists()

    def _ensure_database_exists(self) -> None:
        """Ensure database file and directory exist."""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection.

        Returns:
            SQLite connection
        """
        conn = sqlite3.connect(self.db_path)
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def create_process(  # noqa: PLR0913
        self,
        command: str,
        command_id: str,
        pid: int,
        status: str,
        process_type: str,
        args: dict | None = None,
        start_time: datetime | None = None,
    ) -> int:
        """Create a new process record.

        Args:
            command: Command string that was executed
            command_id: Unique command identifier
            pid: Process ID
            status: Process status (running, success, failed)
            process_type: Type of process (backup, restore, cleanup_backups, etc.)
            args: Optional dictionary of additional arguments
            start_time: Process start time (defaults to now)

        Returns:
            Process ID (database row ID)
        """
        if start_time is None:
            from datetime import UTC  # noqa: PLC0415

            start_time = datetime.now(tz=UTC)
        if args is None:
            args = {}

        # Convert datetime to ISO format for SQLite storage
        start_time_str = start_time.isoformat()

        # Convert args dict to JSON
        args_json = json.dumps(args)

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO process (
                    command, command_id, pid, status, start_time,
                    type, args
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    command,
                    command_id,
                    pid,
                    status,
                    start_time_str,
                    process_type,
                    args_json,
                ),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def update_process_status(  # noqa: PLR0913
        self,
        process_id: int,
        status: str,
        output: str | None = None,
        error: str | None = None,
        return_code: int | None = None,
        end_time: datetime | None = None,
    ) -> None:
        """Update process status and completion info.

        Args:
            process_id: Process database ID
            status: New status (running, success, failed)
            output: Optional command output
            error: Optional error message
            return_code: Optional command return code
            end_time: Optional end time (defaults to now if status is terminal)
        """
        # If status is terminal (success/failed) and no end_time, use now
        if end_time is None and status in ("success", "failed"):
            from datetime import UTC  # noqa: PLC0415

            end_time = datetime.now(tz=UTC)

        # Convert end_time to ISO format if present
        end_time_str = end_time.isoformat() if end_time else None

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE process
                SET status = ?,
                    output = COALESCE(?, output),
                    error = COALESCE(?, error),
                    return_code = COALESCE(?, return_code),
                    end_time = COALESCE(?, end_time)
                WHERE id = ?
                """,
                (status, output, error, return_code, end_time_str, process_id),
            )
            conn.commit()
        finally:
            conn.close()

    def get_process(self, process_id: int) -> dict | None:
        """Get process record by ID.

        Args:
            process_id: Process database ID

        Returns:
            Dictionary with process data, or None if not found
        """
        conn = self._get_connection()
        try:
            # Use row factory to get dict-like results
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, command, command_id, pid, status, output, error,
                       return_code, start_time, end_time, type, args
                FROM process
                WHERE id = ?
                """,
                (process_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None

            # Convert row to dict and parse JSON args
            result = dict(row)
            if result["args"]:
                result["args"] = json.loads(result["args"])
            else:
                result["args"] = {}

            return result
        finally:
            conn.close()
