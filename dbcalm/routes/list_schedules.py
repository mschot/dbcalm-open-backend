from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from dbcalm.api.model.query.schedule_query import (
    ScheduleOrderField,
    ScheduleQueryField,
)
from dbcalm.auth.verify_token import verify_token
from dbcalm.data.repository.schedule import ScheduleRepository
from dbcalm.util.parse_query_with_operators import parse_query_with_operators

router = APIRouter()


@router.get("/schedules")
async def list_schedules(
    _: Annotated[dict, Depends(verify_token)],
    query: Annotated[
        str | None,
        Query(
            description=(
                "Filter schedules using format 'field|value' or "
                "'field|operator|value'. "
                "Operators: eq, ne, gt, gte, lt, lte, in, nin. "
                f"Valid fields: {', '.join([f.value for f in ScheduleQueryField])}"
            ),
            openapi_examples={
                "enabled_only": {
                    "summary": "Filter enabled schedules",
                    "value": "enabled|true",
                },
                "by_frequency": {
                    "summary": "Filter by frequency",
                    "value": "frequency|daily",
                },
                "by_backup_type": {
                    "summary": "Filter by backup type",
                    "value": "backup_type|full",
                },
            },
        ),
    ] = None,
    order: Annotated[
        str | None,
        Query(
            description=(
                "Order results using format 'field|direction'. "
                f"Valid fields: {', '.join([f.value for f in ScheduleOrderField])}. "
                "Direction: asc or desc"
            ),
            openapi_examples={
                "newest_first": {
                    "summary": "Newest first",
                    "value": "created_at|desc",
                },
                "by_enabled": {
                    "summary": "Enabled first",
                    "value": "enabled|desc",
                },
            },
        ),
    ] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=1000)] = 25,
) -> dict[str, Any]:
    repository = ScheduleRepository()
    query_filters = parse_query_with_operators(query)
    order_filters = parse_query_with_operators(order)

    # Validate field names using enums
    valid_query_fields = {f.value for f in ScheduleQueryField}
    for f in query_filters:
        if f.field not in valid_query_fields:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid query field: {f.field}. "
                    f"Valid fields: {', '.join(valid_query_fields)}"
                ),
            )

    valid_order_fields = {f.value for f in ScheduleOrderField}
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
