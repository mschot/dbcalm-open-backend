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

@router.post("/backups")
async def create_backup(
    request: BackupRequest,
    response: Response,
    _: Annotated[dict, Depends(verify_token)],
) -> StatusResponse :
    client = Client()

    if request.id is None:
        id = datetime.now(tz=UTC).strftime("%Y-%m-%d-%H-%M-%S")
    else:
        id = kebab_case(id)

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

    return process_status_response(process, response)


