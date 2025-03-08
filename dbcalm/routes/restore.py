from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from dbcalm.api.model.response.status_response import StatusResponse
from dbcalm.auth.verify_token import verify_token
from dbcalm.data.data_types.enum_types import RestoreTarget
from dbcalm.data.model.backup import Backup
from dbcalm.data.repository.backup import BackupRepository
from dbcalm.util.process_status_response import process_status_response
from dbcalm_cmd_client.client import Client


def get_previous_backups(backup: Backup) -> list[Backup]:
    all_backups = [backup.identifier]
    current = backup
    while current.from_identifier:
        prev_backup = BackupRepository().get(current.from_identifier)
        if prev_backup:
            all_backups.append(prev_backup.identifier)
            current = prev_backup
        else:
            msg = f"Backup with identifier {current.from_identifier} not found"
            raise HTTPException(status_code=404, detail=msg)

    all_backups.reverse()
    return all_backups



class RestoreRequest(BaseModel):
    identifier: str
    target: RestoreTarget

router = APIRouter()
@router.post("/restore")
async def restore_backup(
    request: RestoreRequest,
    _: Annotated[dict, Depends(verify_token)],
    response: Response,
) -> StatusResponse:
    backup = BackupRepository().get(request.identifier)
    if backup is None:
        msg = f"Backup with identifier {request.identifier} not found"
        raise HTTPException(status_code=404, detail=msg)

    # Get all backups needed to restore from the base backup to the current one
    # will return current identifier only if not an incremental backup
    backups = get_previous_backups(backup)

    client = Client()
    process = client.command(
        "restore_backup",
        {"identifier_list": backups, "target": request.target},
    )

    return process_status_response(process, response)
