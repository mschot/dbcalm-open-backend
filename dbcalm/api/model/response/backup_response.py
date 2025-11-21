from datetime import datetime

from pydantic import ConfigDict, Field

from dbcalm.api.model.response.base_response import BaseResponse
from dbcalm.api.model.response.list_response import PaginationInfo


class BackupResponse(BaseResponse):
    model_config = ConfigDict(from_attributes=True)
    """Response model for a single backup."""

    id: str = Field(description="Unique backup identifier")
    from_backup_id: str | None = Field(
        description=(
            "ID of the base backup for incremental backups, null for full backups"
        ),
    )
    start_time: datetime = Field(description="When the backup started")
    end_time: datetime | None = Field(
        description="When the backup completed (null if still running)",
    )
    process_id: int = Field(description="ID of the process that created this backup")
    schedule_id: int | None = Field(
        default=None,
        description=(
            "ID of the schedule that created this backup "
            "(null for manual backups)"
        ),
    )
    retention_value: int | None = Field(
        default=None,
        description=(
            "Retention value from the schedule "
            "(null if no retention or manual backup)"
        ),
    )
    retention_unit: str | None = Field(
        default=None,
        description=(
            "Retention unit from the schedule "
            "(days/weeks/months, null if no retention or manual backup)"
        ),
    )


class BackupListResponse(BaseResponse):
    """Response model for paginated list of backups."""

    items: list[BackupResponse] = Field(description="List of backups")
    pagination: PaginationInfo = Field(description="Pagination metadata")
