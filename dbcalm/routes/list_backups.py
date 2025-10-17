from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from dbcalm.api.model.query.backup_query import (
    BackupOrderField,
    BackupQueryField,
)
from dbcalm.auth.verify_token import verify_token
from dbcalm.data.repository.backup import BackupRepository
from dbcalm.util.parse_query_with_operators import parse_query_with_operators

router = APIRouter()
@router.get("/backups")
async def list_backups(
    _: Annotated[dict, Depends(verify_token)],
    query: Annotated[
        str | None,
        Query(
            description=(
                "Filter backups using format 'field|value' or "
                "'field|operator|value'. "
                "Operators: eq, ne, gt, gte, lt, lte, in, nin. "
                f"Valid fields: {', '.join([f.value for f in BackupQueryField])}"
            ),
            openapi_examples={
                "by_id": {
                    "summary": "Filter by ID",
                    "value": "id|2024-10-17-12-00-00",
                },
                "by_date_range": {
                    "summary": "Filter by start time",
                    "value": "start_time|gte|2024-10-01T00:00:00",
                },
                "by_process_list": {
                    "summary": "Filter by process IDs",
                    "value": "process_id|in|1,2,3",
                },
            },
        ),
    ] = None,
    order: Annotated[
        str | None,
        Query(
            description=(
                "Order results using format 'field|direction'. "
                f"Valid fields: {', '.join([f.value for f in BackupOrderField])}. "
                "Direction: asc or desc"
            ),
            openapi_examples={
                "newest_first": {
                    "summary": "Newest first",
                    "value": "start_time|desc",
                },
                "oldest_first": {
                    "summary": "Oldest first",
                    "value": "start_time|asc",
                },
            },
        ),
    ] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=1000)] = 25,
) -> dict[str, Any]:
    repository = BackupRepository()
    query_filters = parse_query_with_operators(query)
    order_filters = parse_query_with_operators(order)

    # Validate field names using enums
    valid_query_fields = {f.value for f in BackupQueryField}
    for f in query_filters:
        if f.field not in valid_query_fields:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid query field: {f.field}. "
                    f"Valid fields: {', '.join(valid_query_fields)}"
                ),
            )

    valid_order_fields = {f.value for f in BackupOrderField}
    for f in order_filters:
        if f.field not in valid_order_fields:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid order field: {f.field}. "
                    f"Valid fields: {', '.join(valid_order_fields)}"
                ),
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
