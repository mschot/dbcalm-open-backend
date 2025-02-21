from typing import Annotated, Any

from fastapi import APIRouter, Depends

from backrest.auth.verify_token import verify_token

router = APIRouter()
@router.get("/backups")
async def list_backups(
    _: Annotated[dict, Depends(verify_token)],
) -> dict[str, Any]:
    return {"message": "backups"}
