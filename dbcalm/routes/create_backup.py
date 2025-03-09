from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Response

from dbcalm.api.model.request.backup_request import BackupRequest
from dbcalm.api.model.response.status_response import StatusResponse
from dbcalm.auth.verify_token import verify_token
from dbcalm.util.kebab import kebab_case
from dbcalm.util.process_status_response import process_status_response
from dbcalm_cmd_client.client import Client

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

    # Support both from_backup_id and from_backup_id for backward compatibility
    from_backup_id = request.from_backup_id

    if from_backup_id is None:
        process = client.command("full_backup", {"id": id})
    else:
        process = client.command(
            "incremental_backup",
            {"id": id, "from_backup_id": from_backup_id},
        )

    return process_status_response(process, response)


