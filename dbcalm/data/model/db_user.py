"""Database User model.

This is a Peewee database model for User.
Uses the same database table structure.
"""

from datetime import datetime

from peewee import CharField, DateTimeField, Model

from dbcalm.data.database.peewee_db import db


class DbUser(Model):
    """User model using Peewee ORM.

    Uses the 'user' table in the database.
    Uses the 'user' table in the database.
    """

    username = CharField(primary_key=True)
    password = CharField()
    created_at = DateTimeField()
    updated_at = DateTimeField()

    class Meta:
        database = db
        table_name = "user"

    def to_dict(self) -> dict:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of the model
        """
        return {
            "username": self.username,
            "password": self.password,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DbUser":
        """Create model from dictionary.

        Args:
            data: Dictionary with model data

        Returns:
            New UserPeewee instance
        """
        # Convert datetime strings to datetime objects if needed
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])

        return cls(**data)
