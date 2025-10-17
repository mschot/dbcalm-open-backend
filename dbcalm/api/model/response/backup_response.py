from datetime import datetime

from pydantic import BaseModel, Field

from dbcalm.api.model.response.list_response import PaginationInfo


class BackupResponse(BaseModel):
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


class BackupListResponse(BaseModel):
    """Response model for paginated list of backups."""

    items: list[BackupResponse] = Field(description="List of backups")
    pagination: PaginationInfo = Field(description="Pagination metadata")
