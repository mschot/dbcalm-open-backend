from datetime import datetime

from pydantic import BaseModel, Field

from dbcalm.api.model.response.list_response import PaginationInfo


class ProcessResponse(BaseModel):
    """Response model for a single process."""

    id: int = Field(description="Unique process identifier")
    command: str = Field(description="Command that was executed")
    command_id: str = Field(description="Command type identifier")
    pid: int = Field(description="Operating system process ID")
    status: str = Field(description="Process status (running, completed, failed, etc.)")
    output: str | None = Field(description="Standard output from the process")
    error: str | None = Field(description="Error output from the process")
    return_code: int | None = Field(
        description="Process exit code (null if still running)",
    )
    start_time: datetime = Field(description="When the process started")
    end_time: datetime | None = Field(
        description="When the process completed (null if still running)",
    )
    type: str = Field(description="Type of process (backup, restore, etc.)")
    args: dict = Field(description="Arguments passed to the command")


class ProcessListResponse(BaseModel):
    """Response model for paginated list of processes."""

    items: list[ProcessResponse] = Field(description="List of processes")
    pagination: PaginationInfo = Field(description="Pagination metadata")
