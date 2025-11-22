"""Database AuthCode model.

This is the Peewee database model for AuthCode.
Uses the same database table structure.
"""

import json

from peewee import CharField, IntegerField, Model, TextField

from dbcalm.data.database.peewee_db import db


class DbAuthCode(Model):
    """AuthCode database model using Peewee ORM.

    Uses the 'authcode' table in the database.
    """

    code = CharField(primary_key=True)
    username = CharField()
    scopes = TextField()  # Stored as JSON string
    expires_at = IntegerField()

    class Meta:
        database = db
        table_name = "authcode"

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
            "code": self.code,
            "username": self.username,
            "scopes": self.get_scopes(),
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DbAuthCode":
        """Create model from dictionary.

        Args:
            data: Dictionary with model data

        Returns:
            New DbAuthCode instance
        """
        # Handle scopes conversion
        scopes = data.pop("scopes", [])
        instance = cls(**data)
        instance.set_scopes(scopes)
        return instance
