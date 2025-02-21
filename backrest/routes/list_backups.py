from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from backrest.auth.verify_token import verify_token
from backrest.data.repository.backup import BackupRepository

router = APIRouter()
@router.get("/backups")
async def list_backups(
    _: Annotated[dict, Depends(verify_token)],
    query: dict | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> dict[str, Any]:
    repository = BackupRepository()
    items, total = repository.list(query, page=page, per_page=per_page)

    return {
        "items": [item.model_dump() for item in items],
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
        },
    }
