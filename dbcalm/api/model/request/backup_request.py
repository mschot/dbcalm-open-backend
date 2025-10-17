from pydantic import BaseModel, Field

from dbcalm.data.data_types.enum_types import BackupType


class BackupRequest(BaseModel):
    """Request to create a new backup."""

    type: BackupType = Field(
        ...,
        description=(
            "Type of backup: 'full' (complete backup) or "
            "'incremental' (changes since base backup)"
        ),
    )
    id: str | None = Field(
        None,
        description=(
            "Optional custom ID for the backup. "
            "Auto-generated timestamp (YYYY-MM-DD-HH-MM-SS) if not provided"
        ),
    )
    from_backup_id: str | None = Field(
        None,
        description=(
            "For incremental backups: ID of the base backup. "
            "Auto-detected (uses latest backup) if not provided"
        ),
    )


