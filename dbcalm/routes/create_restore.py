from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from dbcalm.api.model.response.status_response import StatusResponse
from dbcalm.auth.verify_token import verify_token
from dbcalm.data.data_types.enum_types import RestoreTarget
from dbcalm.data.repository.backup import BackupRepository
from dbcalm.errors.not_found_error import NotFoundError
from dbcalm.util.process_status_response import process_status_response
from dbcalm_mariadb_cmd_client.client import Client


class RestoreRequest(BaseModel):
    """Request to restore a backup."""

    id: str = Field(..., description="ID of the backup to restore")
    target: RestoreTarget = Field(
        ...,
        description=(
            "Restore target: 'database' (to MySQL data dir) or "
            "'folder' (to custom folder for inspection)"
        ),
    )

router = APIRouter()
@router.post(
    "/restore",
    status_code=202,
    responses={
        202: {
            "description": "Restore accepted and started - processing in background",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/StatusResponse"},
                },
            },
        },
        404: {
            "description": "Backup not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Backup with id xyz not found"},
                },
            },
        },
        503: {
            "description": "Service unavailable - server configuration issue",
            "content": {
                "application/json": {
                    "examples": {
                        "server_running": {
                            "summary": "MySQL server still running",
                            "value": {
                                "detail": (
                                    "cannot restore to database, "
                                    "MySQL/MariaDb server is not stopped"
                                ),
                            },
                        },
                        "data_dir_not_empty": {
                            "summary": "Data directory not empty",
                            "value": {
                                "detail": (
                                    "cannot restore to database, mysql/mariadb "
                                    "data directory is not empty "
                                    "(usually /var/lib/mysql)"
                                ),
                            },
                        },
                        "credentials_missing": {
                            "summary": "Credentials file missing",
                            "value": {
                                "detail": (
                                    "credentials file not found or "
                                    "missing [client-dbcalm] section"
                                ),
                            },
                        },
                    },
                },
            },
        },
    },
)
async def create_restore(
    request: RestoreRequest,
    _: Annotated[dict, Depends(verify_token)],
    response: Response,
) -> StatusResponse:
    """
    Restore a backup to database or folder.

    **This is an asynchronous operation** - returns 202 Accepted immediately
    and the restore runs in the background. Use the returned `link` to poll
    for completion status at `/status/{pid}`.

    Restores a backup and all its dependencies to either the MySQL data directory
    or a custom folder for inspection. For incremental backups, all required base
    backups are automatically included in the restore operation.

    **Requirements for database restore:**
    - MySQL/MariaDB server must be stopped
    - Data directory must be empty
    - Valid credentials file must exist

    **For folder restore:**
    - No special requirements, data is restored to a temporary inspection folder

    **Response:**
    - Returns immediately with 202 Accepted
    - Includes `link` field pointing to `/status/{pid}` for progress tracking
    - Includes `resource_id` (the backup ID being restored)
    """
    backup = BackupRepository().get(request.id)
    if backup is None:
        msg = f"Backup with id {request.id} not found"
        raise HTTPException(status_code=404, detail=msg)

    # Get all backups needed to restore from the base backup to the current one
    # will return current id only if not an incremental backup
    try:
        backups = BackupRepository().required_backups(backup)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    client = Client()
    process = client.command(
        "restore_backup",
        {"id_list": backups, "target": request.target},
    )

    return process_status_response(process, response, resource_id=request.id)
