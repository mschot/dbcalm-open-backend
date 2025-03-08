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

    if request.identifier is None:
        identifier = datetime.now(tz=UTC).strftime("%Y-%m-%d-%H-%M-%S")
    else:
        identifier = kebab_case(identifier)

    if request.from_identifier is None:
        process = client.command("full_backup", {"identifier": identifier})
    else:
        process = client.command(
            "incremental_backup",
            {"identifier": identifier, "from_identifier": request.from_identifier},
        )

    return process_status_response(process, response)


