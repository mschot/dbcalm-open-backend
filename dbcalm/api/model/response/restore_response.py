from datetime import datetime

from pydantic import Field

from dbcalm.api.model.response.base_response import BaseResponse
from dbcalm.api.model.response.list_response import PaginationInfo
from dbcalm.data.data_types.enum_types import RestoreTarget


class RestoreResponse(BaseResponse):
    """Response model for a single restore."""

    id: int = Field(description="Unique restore identifier")
    start_time: datetime = Field(description="When the restore started")
    end_time: datetime | None = Field(
        description="When the restore completed (null if still running)",
    )
    target: RestoreTarget = Field(
        description="Restore target (database or folder)",
    )
    target_path: str = Field(description="Path where data was restored")
    backup_id: str = Field(description="ID of the backup that was restored")
    backup_timestamp: datetime | None = Field(
        description="Timestamp of the backup",
    )
    process_id: int = Field(description="ID of the restore process")


class RestoreListResponse(BaseResponse):
    """Response model for paginated list of restores."""

    items: list[RestoreResponse] = Field(description="List of restores")
    pagination: PaginationInfo = Field(description="Pagination metadata")
