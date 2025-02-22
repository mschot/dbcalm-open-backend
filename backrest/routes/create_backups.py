from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Response

from backrest.api.model.request.backup_request import BackupRequest
from backrest.api.model.response.status_response import StatusResponse
from backrest.auth.verify_token import verify_token
from backrest.util.kebab import kebab_case
from backrest_client.client import Client

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

    accepted_code = 202
    if process["code"] == accepted_code:
        response.status_code = accepted_code
        pid = str(process["pid"]) + process["created_at"]
        return StatusResponse(
            pid = pid,
            link = f"/status/{pid}",
            status=process["status"],
        )
    response.status_code = 500
    return StatusResponse(status="Error")
