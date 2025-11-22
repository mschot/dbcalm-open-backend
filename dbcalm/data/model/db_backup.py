"""Database Backup model.

This is the Peewee database model for Backup.
Uses the same database table structure.
"""

from datetime import datetime

from peewee import CharField, DateTimeField, IntegerField, Model

from dbcalm.data.database.peewee_db import db


class DbBackup(Model):
    """Backup database model using Peewee ORM.

    Uses the 'backup' table in the database.
    """

    id = CharField(primary_key=True)
    from_backup_id = CharField(null=True)
    schedule_id = IntegerField(null=True)
    start_time = DateTimeField()
    end_time = DateTimeField(null=True)
    process_id = IntegerField()

    class Meta:
        database = db
        table_name = "backup"

    def to_dict(self) -> dict:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of the model
        """
        return {
            "id": self.id,
            "from_backup_id": self.from_backup_id,
            "schedule_id": self.schedule_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "process_id": self.process_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DbBackup":
        """Create model from dictionary.

        Args:
            data: Dictionary with model data

        Returns:
            New DbBackup instance
        """
        # Convert datetime strings to datetime objects if needed
        if isinstance(data.get("start_time"), str):
            data["start_time"] = datetime.fromisoformat(data["start_time"])
        if isinstance(data.get("end_time"), str):
            data["end_time"] = datetime.fromisoformat(data["end_time"])

        return cls(**data)
