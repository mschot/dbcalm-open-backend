"""Database Restore model.

This is a Peewee database model for Restore.
Uses the same database table structure.
"""

from datetime import datetime

from peewee import CharField, DateTimeField, IntegerField, Model

from dbcalm.data.database.peewee_db import db


class DbRestore(Model):
    """Restore model using Peewee ORM.

    Uses the 'restore' table in the database.
    Uses the 'restore' table in the database.
    """

    id = IntegerField(primary_key=True)
    start_time = DateTimeField()
    end_time = DateTimeField(null=True)
    target = CharField()  # RestoreTarget enum stored as string
    target_path = CharField()
    backup_id = CharField()
    backup_timestamp = DateTimeField(null=True)
    process_id = IntegerField()

    class Meta:
        database = db
        table_name = "restore"

    def to_dict(self) -> dict:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of the model
        """
        return {
            "id": self.id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "target": self.target,
            "target_path": self.target_path,
            "backup_id": self.backup_id,
            "backup_timestamp": (
                self.backup_timestamp.isoformat() if self.backup_timestamp else None
            ),
            "process_id": self.process_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DbRestore":
        """Create model from dictionary.

        Args:
            data: Dictionary with model data

        Returns:
            New RestorePeewee instance
        """
        # Convert datetime strings to datetime objects if needed
        if isinstance(data.get("start_time"), str):
            data["start_time"] = datetime.fromisoformat(data["start_time"])
        if isinstance(data.get("end_time"), str):
            data["end_time"] = datetime.fromisoformat(data["end_time"])
        if isinstance(data.get("backup_timestamp"), str):
            data["backup_timestamp"] = datetime.fromisoformat(data["backup_timestamp"])

        return cls(**data)
