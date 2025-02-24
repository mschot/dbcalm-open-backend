from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from backrest.api.model.response.status_response import StatusResponse
from backrest.auth.verify_token import verify_token
from backrest.data.model.backup import Backup
from backrest.data.repository.backup import BackupRepository
from backrest_client.client import Client


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

    backups = get_previous_backups(backup)

    client = Client()
    process = client.command(
        "restore_backup",
        {"identifier_list": backups},
    )

    accepted_code = 202
    if process["code"] == accepted_code:
        response.status_code = accepted_code
        return StatusResponse(
            pid = process["id"],
            link = f"/status/{process["id"]}",
            status=process["status"],
        )
    response.status_code = 500
    return StatusResponse(status="Error")
