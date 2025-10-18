from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from dbcalm.api.model.query.schedule_query import (
    ScheduleOrderField,
    ScheduleQueryField,
)
from dbcalm.api.model.response.list_response import PaginationInfo
from dbcalm.api.model.response.schedule_response import (
    ScheduleListResponse,
    ScheduleResponse,
)
from dbcalm.auth.verify_token import verify_token
from dbcalm.data.repository.schedule import ScheduleRepository
from dbcalm.util.parse_query_with_operators import parse_query_with_operators

router = APIRouter()


@router.get(
    "/schedules",
    responses={
        200: {
            "description": "List of schedules",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": 1,
                                "backup_type": "full",
                                "frequency": "daily",
                                "day_of_week": None,
                                "day_of_month": None,
                                "hour": 3,
                                "minute": 0,
                                "interval_value": None,
                                "interval_unit": None,
                                "enabled": True,
                                "created_at": "2024-10-15T10:30:00",
                                "updated_at": "2024-10-15T10:30:00",
                            },
                            {
                                "id": 2,
                                "backup_type": "incremental",
                                "frequency": "interval",
                                "day_of_week": None,
                                "day_of_month": None,
                                "hour": None,
                                "minute": None,
                                "interval_value": 6,
                                "interval_unit": "hours",
                                "enabled": True,
                                "created_at": "2024-10-16T14:15:00",
                                "updated_at": "2024-10-16T14:15:00",
                            },
                        ],
                        "pagination": {
                            "total": 5,
                            "page": 1,
                            "per_page": 25,
                            "total_pages": 1,
                        },
                    },
                },
            },
        },
    },
)
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
) -> ScheduleListResponse:
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

    return ScheduleListResponse(
        items=[ScheduleResponse(**item.model_dump()) for item in items],
        pagination=PaginationInfo(
            total=total,
            page=page,
            per_page=per_page,
            total_pages=(total + per_page - 1) // per_page,
        ),
    )
