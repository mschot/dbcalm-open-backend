from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from dbcalm.auth.verify_token import verify_token
from dbcalm.data.model.backup import Backup
from dbcalm.data.repository.backup import BackupRepository
from dbcalm.util.parse_query_with_operators import parse_query_with_operators

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
    query_filters = parse_query_with_operators(query)
    order_filters = parse_query_with_operators(order)

    # Validate field names for query filters
    for f in query_filters:
        if not hasattr(Backup, f.field):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid query field: {f.field}",
            )

    # Validate field names for order filters
    for f in order_filters:
        if not hasattr(Backup, f.field):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid order field: {f.field}",
            )

    items, total = repository.get_list(
        query_filters,
        order_filters,
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
