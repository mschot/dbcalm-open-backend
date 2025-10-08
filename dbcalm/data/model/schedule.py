
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def now() -> datetime:
    return datetime.now(tz=UTC)


class Schedule(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(nullable=False)
    backup_type: str = Field(nullable=False)  # "full" or "incremental"
    frequency: str = Field(nullable=False)  # "daily", "weekly", "monthly"
    day_of_week: int | None = None  # 0-6 (0=Sunday), only for weekly
    day_of_month: int | None = None  # 1-28, only for monthly
    hour: int = Field(nullable=False)  # 0-23
    minute: int = Field(nullable=False)  # 0-59
    enabled: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(default_factory=now, nullable=False)
    updated_at: datetime = Field(default_factory=now, nullable=False)


Schedule.model_rebuild()
