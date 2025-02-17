
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def now() -> datetime:
    return datetime.now(tz=timezone.utc)

class Backup(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    identifier: str
    from_identifier: Optional[str] = None
    start_time: datetime = Field(
        default_factory=now,
        nullable=False,
    )
    end_time: Optional[datetime] = None


