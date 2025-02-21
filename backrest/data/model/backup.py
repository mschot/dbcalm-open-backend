
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def now() -> datetime:
    return datetime.now(tz=UTC)

class Backup(SQLModel, table=True):
    identifier: str = Field(primary_key=True)
    from_identifier: str | None = None
    start_time: datetime = Field(
        default_factory=now,
        nullable=False,
    )
    end_time: datetime | None = None


