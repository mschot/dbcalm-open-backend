from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from dbcalm.auth.verify_token import verify_token
from dbcalm.data.model.backup import Backup
from dbcalm.data.repository.backup import BackupRepository
from dbcalm.util.has_attributes_for_dict_keys import (
    has_attributes_for_dict_keys,
)
from dbcalm.util.parse_query_dict import parse_query_dict

router = APIRouter()
@router.get("/backups")
async def list_backups(
    _: Annotated[dict, Depends(verify_token)],
    query: str | None = None,
    order: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=1000)] = 25,
) -> dict[str, Any]:
    repository = BackupRepository()
    query_dict = parse_query_dict(query)
    if not has_attributes_for_dict_keys(Backup, query_dict):
        raise HTTPException(status_code=400, detail="Invalid query attribute")

    order_dict = parse_query_dict(order)
    if not has_attributes_for_dict_keys(Backup, order_dict):
        raise HTTPException(status_code=400, detail="Invalid order attribute")

    items, total = repository.get_list(
        query_dict,
        order_dict,
        page=page,
        per_page=per_page,
    )

    return {
        "items": [item.model_dump() for item in items],
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
        },
    }
