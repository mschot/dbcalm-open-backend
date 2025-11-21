from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Response

from dbcalm.api.model.request.cleanup_request import CleanupRequest
from dbcalm.api.model.response.status_response import StatusResponse
from dbcalm.auth.verify_token import verify_token
from dbcalm.config.config_factory import config_factory
from dbcalm.data.repository.backup import BackupRepository
from dbcalm.data.repository.schedule import ScheduleRepository
from dbcalm.service.backup_retention_policy import BackupRetentionPolicy
from dbcalm.util.process_status_response import process_status_response
from dbcalm_cmd_client.client import Client

router = APIRouter()


@router.post(
    "/cleanup",
    status_code=202,
    responses={
        202: {
            "description": "Cleanup accepted and started - processing in background",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/StatusResponse"},
                    "example": {
                        "status": "running",
                        "link": "/status/1234",
                        "pid": "1234",
                        "resource_id": "1",
                    },
                },
            },
        },
        404: {
            "description": "Schedule not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Schedule 123 not found",
                    },
                },
            },
        },
    },
)
async def cleanup_backups(
    request: Annotated[
        CleanupRequest,
        Body(
            openapi_examples={
                "cleanup_all": {
                    "summary": "Clean up all schedules",
                    "description": (
                        "Run cleanup for all schedules with retention policies"
                    ),
                    "value": {},
                },
                "cleanup_specific": {
                    "summary": "Clean up specific schedule",
                    "description": "Run cleanup for a specific schedule",
                    "value": {
                        "schedule_id": 1,
                    },
                },
            },
        ),
    ],
    response: Response,
    _: Annotated[dict, Depends(verify_token)],
) -> StatusResponse:
    """
    Run backup cleanup based on retention policies.

    **This is an asynchronous operation** - returns 202 Accepted immediately
    and the cleanup runs in the background. Use the returned `link` to poll
    for completion status at `/status/{pid}`.

    Cleans up old backups according to schedule retention policies. If no
    schedule_id is provided, cleans up all schedules with retention policies.

    **Response:**
    - Returns immediately with 202 Accepted
    - Includes `link` field for progress tracking at `/status/{pid}`
    - Includes `resource_id` (schedule_id if provided)
    """
    config = config_factory()
    backup_repo = BackupRepository()
    retention_policy = BackupRetentionPolicy(backup_repo)

    # If schedule_id provided, verify it exists
    if request.schedule_id is not None:
        schedule_repo = ScheduleRepository()
        schedule = schedule_repo.get(request.schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=404,
                detail=f"Schedule {request.schedule_id} not found",
            )

    # Get list of backups that require cleaning
    backups_to_delete = retention_policy.get_expired_backups(request.schedule_id)

    if not backups_to_delete:
        # No backups to delete - return success immediately
        # Create a fake process response for consistency
        return StatusResponse(
            status="success",
            link=None,
            pid=None,
            resource_id=str(request.schedule_id) if request.schedule_id else None,
        )

    # Extract backup IDs and folder paths
    backup_ids = [backup.id for backup in backups_to_delete]
    backup_dir = config.value("backup_dir").rstrip("/")
    folders = [f"{backup_dir}/{backup.id}" for backup in backups_to_delete]

    # Send command to generic command service to delete folders
    client = Client()
    process = client.command(
        "cleanup_backups",
        {
            "backup_ids": backup_ids,
            "folders": folders,
        },
    )

    return process_status_response(
        process,
        response,
        resource_id=str(request.schedule_id) if request.schedule_id else None,
    )
