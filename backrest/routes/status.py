from typing import Annotated

from fastapi import APIRouter, Depends

from backrest.api.model.response.status_request import StatusResponse
from backrest.auth.verify_token import verify_token

router = APIRouter()

@router.get("/status/{status_id}")
async def get_status(
    status_id: int,
    _: Annotated[dict, Depends(verify_token)],
) -> StatusResponse:
    return {
        "id": status_id,
        "status": "completed",
        "type": "backup",
        "link": "/backups/{backup_id}",
    }
