# backrest/data/model/restore.py

from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlmodel import Column, Field, SQLModel

from dbcalm.data.data_types.enum_types import RestoreTarget


def now() -> datetime:
    return datetime.now(tz=UTC)


class Restore(SQLModel, table=True):
    """Restore database model."""
    id: int | None = Field(default=None, primary_key=True)
    start_time: datetime = Field(
        default_factory=now, sa_column=Column(DateTime(timezone=True)),
    )
    end_time: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True)),
    )
    target: RestoreTarget
    target_path: str
    backup_id: str
    backup_timestamp: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True)),
    )
    process_id: int


