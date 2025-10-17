from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

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
    request: BackupRequest,
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

    if from_backup_id is not None:
        process = client.command(
            "incremental_backup",
            {"id": id, "from_backup_id": from_backup_id},
        )
    else:
        process = client.command("full_backup", {"id": id})

    return process_status_response(process, response, resource_id=id)


