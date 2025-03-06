from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from dbcalm.api.model.response.status_response import StatusResponse
from dbcalm.auth.verify_token import verify_token
from dbcalm.data.model.backup import Backup
from dbcalm.data.repository.backup import BackupRepository
from dbcalm.data.types.enum_types import RestoreTarget
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


INVALID_REQUEST = 400
INTERNAL_ERROR = 500

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

    accepted_code = 202
    if process["code"] == accepted_code:
        response.status_code = accepted_code
        return StatusResponse(
            pid = process["id"],
            link = f"/status/{process["id"]}",
            status=process["status"],
        )

    if process["code"] >= INVALID_REQUEST and process["code"] < INTERNAL_ERROR:
        response.status_code = process["code"]
        return StatusResponse(status=str(process["status"]))

    response.status_code = process["code"]
    return StatusResponse(status=str(process["status"]))
