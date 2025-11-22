"""Database Schedule model.

This is a Peewee database model for Schedule.
Uses the same database table structure.
"""

from datetime import datetime

from peewee import (
    BooleanField,
    CharField,
    DateTimeField,
    IntegerField,
    Model,
)

from dbcalm.data.database.peewee_db import db


class DbSchedule(Model):
    """Schedule model using Peewee ORM.

    Uses the 'schedule' table in the database.
    Uses the 'schedule' table in the database.
    """

    id = IntegerField(primary_key=True)
    backup_type = CharField()
    frequency = CharField()
    day_of_week = IntegerField(null=True)
    day_of_month = IntegerField(null=True)
    hour = IntegerField(null=True)
    minute = IntegerField(null=True)
    interval_value = IntegerField(null=True)
    interval_unit = CharField(null=True)
    retention_value = IntegerField(null=True)
    retention_unit = CharField(null=True)
    enabled = BooleanField(default=True)
    created_at = DateTimeField()
    updated_at = DateTimeField()

    class Meta:
        database = db
        table_name = "schedule"

    def to_dict(self) -> dict:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of the model
        """
        return {
            "id": self.id,
            "backup_type": self.backup_type,
            "frequency": self.frequency,
            "day_of_week": self.day_of_week,
            "day_of_month": self.day_of_month,
            "hour": self.hour,
            "minute": self.minute,
            "interval_value": self.interval_value,
            "interval_unit": self.interval_unit,
            "retention_value": self.retention_value,
            "retention_unit": self.retention_unit,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DbSchedule":
        """Create model from dictionary.

        Args:
            data: Dictionary with model data

        Returns:
            New SchedulePeewee instance
        """
        # Convert datetime strings to datetime objects if needed
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])

        return cls(**data)
