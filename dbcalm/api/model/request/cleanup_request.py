from pydantic import BaseModel, Field


class CleanupRequest(BaseModel):
    """Request to run backup cleanup."""

    schedule_id: int | None = Field(
        None,
        description=(
            "Optional schedule ID to clean up. "
            "If not provided, cleans up all schedules with retention policies"
        ),
    )
