"""Database Client model.

This is the Peewee database model for Client.
Uses the same database table structure.
"""

import json

from peewee import CharField, Model, TextField

from dbcalm.data.database.peewee_db import db


class DbClient(Model):
    """Client database model using Peewee ORM.

    Uses the 'client' table in the database.
    """

    id = CharField(primary_key=True, max_length=255)
    secret = CharField(max_length=255)
    scopes = TextField()  # Stored as JSON string
    label = CharField(max_length=255)

    class Meta:
        database = db
        table_name = "client"

    def get_scopes(self) -> list[str]:
        """Get scopes as list.

        Returns:
            Parsed scopes list
        """
        if not self.scopes:
            return []
        return json.loads(self.scopes)

    def set_scopes(self, value: list[str]) -> None:
        """Set scopes from list.

        Args:
            value: List of scopes to store as JSON
        """
        self.scopes = json.dumps(value)

    def to_dict(self) -> dict:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of the model
        """
        return {
            "id": self.id,
            "secret": self.secret,
            "scopes": self.get_scopes(),
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DbClient":
        """Create model from dictionary.

        Args:
            data: Dictionary with model data

        Returns:
            New DbClient instance
        """
        # Handle scopes conversion
        scopes = data.pop("scopes", [])
        instance = cls(**data)
        instance.set_scopes(scopes)
        return instance
