# backrest/data/model/restore.py

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from dbcalm.data.data_types.enum_types import RestoreTarget


def now() -> datetime:
    return datetime.now(tz=UTC)


class Restore(BaseModel):
    """Restore database model."""
    id: int | None = None
    start_time: datetime = Field(default_factory=now)
    end_time: datetime | None = None
    target: RestoreTarget
    target_path: str
    backup_id: str
    backup_timestamp: datetime | None = None
    process_id: int
