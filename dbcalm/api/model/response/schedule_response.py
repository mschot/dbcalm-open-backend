from datetime import datetime

from pydantic import BaseModel, Field

from dbcalm.api.model.response.list_response import PaginationInfo


class ScheduleResponse(BaseModel):
    """Response model for a single schedule."""

    id: int = Field(description="Unique schedule identifier")
    backup_type: str = Field(description="Type of backup (full or incremental)")
    frequency: str = Field(
        description="Schedule frequency (daily, weekly, monthly, hourly, interval)",
    )
    day_of_week: int | None = Field(
        description="Day of week for weekly schedules (0-6, 0=Sunday)",
    )
    day_of_month: int | None = Field(
        description="Day of month for monthly schedules (1-28)",
    )
    hour: int | None = Field(description="Hour for scheduled backups (0-23)")
    minute: int | None = Field(description="Minute for scheduled backups (0-59)")
    interval_value: int | None = Field(
        description="Interval value for interval schedules",
    )
    interval_unit: str | None = Field(
        description="Interval unit (minutes or hours)",
    )
    enabled: bool = Field(description="Whether the schedule is enabled")
    created_at: datetime = Field(description="When the schedule was created")
    updated_at: datetime = Field(description="When the schedule was last updated")


class ScheduleListResponse(BaseModel):
    """Response model for paginated list of schedules."""

    items: list[ScheduleResponse] = Field(description="List of schedules")
    pagination: PaginationInfo = Field(description="Pagination metadata")
