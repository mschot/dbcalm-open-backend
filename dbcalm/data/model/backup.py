
from datetime import UTC, datetime

from pydantic import BaseModel, Field


def now() -> datetime:
    return datetime.now(tz=UTC)

class Backup(BaseModel):
    id: str
    from_backup_id: str | None = None
    schedule_id: int | None = None  # None for manual backups
    start_time: datetime = Field(default_factory=now)
    end_time: datetime | None = None
    process_id: int

