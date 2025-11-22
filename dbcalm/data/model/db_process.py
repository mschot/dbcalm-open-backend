"""Database Process model.

This is a Peewee database model for Process.
Uses the same database table structure.
"""

import json
from datetime import datetime

from peewee import CharField, DateTimeField, IntegerField, Model, TextField

from dbcalm.data.database.peewee_db import db


class DbProcess(Model):
    """Process model using Peewee ORM.

    Uses the 'process' table in the database.
    Uses the 'process' table in the database.
    """

    id = IntegerField(primary_key=True)
    command = TextField()
    command_id = CharField(max_length=255)
    pid = IntegerField()
    status = CharField(max_length=50)
    output = TextField(null=True)
    error = TextField(null=True)
    return_code = IntegerField(null=True)
    start_time = DateTimeField()
    end_time = DateTimeField(null=True)
    type = CharField(max_length=50)
    args = TextField()  # Stored as JSON string

    class Meta:
        database = db
        table_name = "process"

    def get_args(self) -> dict:
        """Get args as dict.

        Returns:
            Parsed args dictionary
        """
        if not self.args:
            return {}
        return json.loads(self.args)

    def set_args(self, value: dict) -> None:
        """Set args from dict.

        Args:
            value: Dictionary to store as JSON
        """
        self.args = json.dumps(value)

    def to_dict(self) -> dict:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of the model
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
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "type": self.type,
            "args": self.get_args(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DbProcess":
        """Create model from dictionary.

        Args:
            data: Dictionary with model data

        Returns:
            New ProcessPeewee instance
        """
        # Convert datetime strings to datetime objects if needed
        if isinstance(data.get("start_time"), str):
            data["start_time"] = datetime.fromisoformat(data["start_time"])
        if isinstance(data.get("end_time"), str):
            data["end_time"] = datetime.fromisoformat(data["end_time"])

        # Handle args conversion
        args = data.pop("args", {})
        instance = cls(**data)
        instance.set_args(args)
        return instance
