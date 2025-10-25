"""Base response class with UTC datetime serialization."""

from datetime import UTC, datetime

from pydantic import BaseModel, model_serializer


class BaseResponse(BaseModel):
    """Base response class with UTC datetime serialization.

    All datetime fields in responses inheriting from this class will be
    serialized with Z suffix for UTC timezone, making it clear to clients
    (especially JavaScript/browsers) that the times are in UTC.

    The browser will automatically convert these to the user's local timezone
    when displaying them.
    """

    @model_serializer(mode="plain", when_used="json-unless-none")
    def serialize_model(self, _info: object) -> dict[str, object]:
        """Serialize model with UTC datetime handling for all datetime fields."""
        # Serialize to Python objects first to preserve datetime objects
        data = self.model_dump(mode="python")

        # Recursively convert all datetime fields to ISO 8601 with Z suffix
        def convert_datetimes(obj: object) -> object:
            if isinstance(obj, dict):
                return {k: convert_datetimes(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [convert_datetimes(item) for item in obj]
            if isinstance(obj, datetime):
                # If naive datetime, assume it's UTC
                if obj.tzinfo is None:
                    obj = obj.replace(tzinfo=UTC)
                # Convert to ISO 8601 with Z suffix instead of +00:00
                return obj.isoformat().replace("+00:00", "Z")
            return obj

        return convert_datetimes(data)
