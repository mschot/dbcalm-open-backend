from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Response

from dbcalm.api.model.request.backup_request import BackupRequest
from dbcalm.api.model.response.status_response import StatusResponse
from dbcalm.auth.verify_token import verify_token
from dbcalm.data.repository.backup import BackupRepository
from dbcalm.util.kebab import kebab_case
from dbcalm.util.process_status_response import process_status_response
from dbcalm_mariadb_cmd_client.client import Client

router = APIRouter()

@router.post(
    "/backups",
    status_code=202,
    responses={
        202: {
            "description": "Backup accepted and started - processing in background",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/StatusResponse"},
                    "example": {
                        "status": "running",
                        "link": "/status/1234",
                        "pid": "1234",
                        "resource_id": "2024-10-18-03-00-00",
                    },
                },
            },
        },
        404: {
            "description": "No existing backups found for incremental backup",
            "content": {
                "application/json": {
                    "example": {
                        "detail": (
                            "No backups found to create incremental backup from"
                        ),
                    },
                },
            },
        },
        503: {
            "description": "Service unavailable - server configuration issue",
            "content": {
                "application/json": {
                    "examples": {
                        "server_not_running": {
                            "summary": "MySQL server not running",
                            "value": {
                                "detail": (
                                    "cannot create backup, "
                                    "MySQL/MariaDB server is not running"
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
async def create_backup(
    request: Annotated[
        BackupRequest,
        Body(
            openapi_examples={
                "full_backup": {
                    "summary": "Full backup with auto-generated ID",
                    "description": "Create a complete backup with timestamp-based ID",
                    "value": {
                        "type": "full",
                    },
                },
                "full_backup_custom_id": {
                    "summary": "Full backup with custom ID",
                    "description": "Create a complete backup with custom identifier",
                    "value": {
                        "type": "full",
                        "id": "production-backup-2024-10-18",
                    },
                },
                "incremental_backup": {
                    "summary": "Incremental backup",
                    "description": "Create incremental backup from latest base backup",
                    "value": {
                        "type": "incremental",
                    },
                },
                "incremental_backup_specific": {
                    "summary": "Incremental backup from specific base",
                    "description": (
                        "Create incremental backup from specific base backup"
                    ),
                    "value": {
                        "type": "incremental",
                        "from_backup_id": "2024-10-17-03-00-00",
                    },
                },
            },
        ),
    ],
    response: Response,
    _: Annotated[dict, Depends(verify_token)],
) -> StatusResponse:
    """
    Create a database backup.

    **This is an asynchronous operation** - returns 202 Accepted immediately
    and the backup runs in the background. Use the returned `link` to poll
    for completion status at `/status/{pid}`.

    Creates either a full or incremental backup of the MySQL/MariaDB database.
    For incremental backups, automatically uses the latest backup as base if
    `from_backup_id` is not specified.

    **Requirements:**
    - MySQL/MariaDB server must be running
    - Valid credentials file must exist
    - For incremental backups: at least one previous backup must exist

    **Backup ID:**
    - Auto-generated timestamp format: YYYY-MM-DD-HH-MM-SS
    - Or provide custom ID (converted to kebab-case)

    **Response:**
    - Returns immediately with 202 Accepted
    - Includes `link` field pointing to `/status/{pid}` for progress tracking
    - Includes `resource_id` (the backup ID)
    """
    client = Client()

    if request.id is None:
        id = datetime.now(tz=UTC).strftime("%Y-%m-%d-%H-%M-%S")
    else:
        id = kebab_case(request.id)

    from_backup_id = request.from_backup_id
    if request.type == "incremental" and from_backup_id is None:

        latest_backup = BackupRepository().latest_backup()
        if not latest_backup:
           raise HTTPException(
            status_code=404,
            detail="No backups found to create incremental backup from",
        )
        from_backup_id = latest_backup.id

    args = {"id": id}
    if request.schedule_id is not None:
        args["schedule_id"] = request.schedule_id

    if from_backup_id is not None:
        args["from_backup_id"] = from_backup_id
        process = client.command("incremental_backup", args)
    else:
        process = client.command("full_backup", args)

    return process_status_response(process, response, resource_id=id)


