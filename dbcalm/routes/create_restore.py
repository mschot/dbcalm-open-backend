from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from dbcalm.api.model.response.status_response import StatusResponse
from dbcalm.auth.verify_token import verify_token
from dbcalm.data.data_types.enum_types import RestoreTarget
from dbcalm.data.repository.backup import BackupRepository
from dbcalm.errors.not_found_error import NotFoundError
from dbcalm.util.process_status_response import process_status_response
from dbcalm_mariadb_cmd_client.client import Client


class RestoreRequest(BaseModel):
    id: str
    target: RestoreTarget

router = APIRouter()
@router.post("/restore")
async def create_restore(
    request: RestoreRequest,
    _: Annotated[dict, Depends(verify_token)],
    response: Response,
) -> StatusResponse:
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

    return process_status_response(process, response)
