from typing import Annotated

from fastapi import APIRouter, Depends

from dbcalm.api.model.response.status_response import StatusResponse
from dbcalm.auth.verify_token import verify_token
from dbcalm.data.repository.process import ProcessRepository

router = APIRouter()

@router.get("/status/{status_id}")
async def get_status(
    status_id: str,
    _: Annotated[dict, Depends(verify_token)],
) -> StatusResponse:

    process_repository = ProcessRepository()
    process = process_repository.by_command_id(status_id)

    # Extract backup/restore ID from process args if available
    resource_id = None
    if process.args and isinstance(process.args, dict):
        resource_id = process.args.get("id")

    return {
        "status": process.status,
        "type": process.type,
        "link": f"/status/{status_id}",
        "resource_id": resource_id,
    }
