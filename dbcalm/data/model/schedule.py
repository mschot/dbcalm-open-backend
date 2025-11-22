
from datetime import UTC, datetime

from pydantic import BaseModel, Field


def now() -> datetime:
    return datetime.now(tz=UTC)


class Schedule(BaseModel):
    id: int | None = None
    backup_type: str  # "full" or "incremental"
    frequency: str  # "daily", "weekly", "monthly", "hourly", "interval"
    day_of_week: int | None = None  # 0-6 (0=Sunday), only for weekly
    day_of_month: int | None = None  # 1-28, only for monthly
    hour: int | None = None  # 0-23, only for non-interval schedules
    minute: int | None = None  # 0-59, only for non-interval schedules
    interval_value: int | None = None  # interval value (e.g., 15, 30, 2)
    interval_unit: str | None = None  # "minutes" or "hours"
    retention_value: int | None = None  # retention period value (e.g., 7, 30, 52)
    retention_unit: str | None = None  # "days", "weeks", "months"
    enabled: bool = True
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)
