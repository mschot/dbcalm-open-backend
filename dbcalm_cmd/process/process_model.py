"""Lightweight Process model for command services.

This module provides a simple dataclass-based Process model that doesn't
require SQLModel or SQLAlchemy, reducing memory footprint for command services.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Process:
    """Lightweight process model for cmd services.

    This is a minimal version of the main Process model (dbcalm.data.model.process)
    that avoids loading SQLModel/SQLAlchemy. It contains only the fields needed
    for command execution and status tracking.
    """

    command: str
    command_id: str
    pid: int
    status: str
    type: str
    id: int | None = None
    output: str | None = None
    error: str | None = None
    return_code: int | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    args: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert Process to dictionary for serialization.

        Returns:
            Dictionary representation with datetime objects as ISO strings
        """
        return {
            "id": self.id,
            "command": self.command,
            "command_id": self.command_id,
            "pid": self.pid,
            "status": self.status,
            "output": self.output,
            "error": self.error,
            "return_code": self.return_code,
            "start_time": (
                self.start_time.isoformat() if self.start_time else None
            ),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "type": self.type,
            "args": self.args,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Process":
        """Create Process from dictionary.

        Args:
            data: Dictionary with process data

        Returns:
            Process instance
        """
        # Parse datetime strings if present
        start_time = data.get("start_time")
        if start_time and isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time)

        end_time = data.get("end_time")
        if end_time and isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time)

        return cls(
            id=data.get("id"),
            command=data["command"],
            command_id=data["command_id"],
            pid=data["pid"],
            status=data["status"],
            output=data.get("output"),
            error=data.get("error"),
            return_code=data.get("return_code"),
            start_time=start_time,
            end_time=end_time,
            type=data["type"],
            args=data.get("args", {}),
        )

    def to_json(self) -> str:
        """Serialize to JSON string.

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "Process":
        """Deserialize from JSON string.

        Args:
            json_str: JSON string with process data

        Returns:
            Process instance
        """
        return cls.from_dict(json.loads(json_str))
