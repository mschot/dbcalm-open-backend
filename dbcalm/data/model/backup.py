
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def now() -> datetime:
    return datetime.now(tz=UTC)

class Backup(SQLModel, table=True):
    id: str = Field(primary_key=True)
    from_backup_id: str | None
    start_time: datetime = Field(
        default_factory=now,
        nullable=False,
    )
    end_time: datetime | None = None
    process_id: int

Backup.model_rebuild()

