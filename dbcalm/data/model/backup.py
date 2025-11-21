
from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlmodel import Column, Field, SQLModel


def now() -> datetime:
    return datetime.now(tz=UTC)

class Backup(SQLModel, table=True):
    id: str = Field(primary_key=True)
    from_backup_id: str | None
    schedule_id: int | None = None  # None for manual backups
    start_time: datetime = Field(
        default_factory=now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    end_time: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True)),
    )
    process_id: int

Backup.model_rebuild()

