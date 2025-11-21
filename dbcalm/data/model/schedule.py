
from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlmodel import Column, Field, SQLModel


def now() -> datetime:
    return datetime.now(tz=UTC)


class Schedule(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    backup_type: str = Field(nullable=False)  # "full" or "incremental"
    # "daily", "weekly", "monthly", "hourly", "interval"
    frequency: str = Field(nullable=False)
    day_of_week: int | None = None  # 0-6 (0=Sunday), only for weekly
    day_of_month: int | None = None  # 1-28, only for monthly
    hour: int | None = None  # 0-23, only for non-interval schedules
    minute: int | None = None  # 0-59, only for non-interval schedules
    interval_value: int | None = None  # interval value (e.g., 15, 30, 2)
    interval_unit: str | None = None  # "minutes" or "hours"
    retention_value: int | None = None  # retention period value (e.g., 7, 30, 52)
    retention_unit: str | None = None  # "days", "weeks", "months"
    enabled: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(
        default_factory=now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


Schedule.model_rebuild()
