from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from dbcalm.api.model.query.process_query import (
    ProcessOrderField,
    ProcessQueryField,
)
from dbcalm.api.model.response.list_response import PaginationInfo
from dbcalm.api.model.response.process_response import (
    ProcessListResponse,
    ProcessResponse,
)
from dbcalm.auth.verify_token import verify_token
from dbcalm.data.repository.process import ProcessRepository
from dbcalm.util.parse_query_with_operators import parse_query_with_operators

router = APIRouter()
@router.get(
    "/processes",
    responses={
        200: {
            "description": "List of processes",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": 1234,
                                "command": (
                                    "mariabackup --backup "
                                    "--target-dir=/var/backups/dbcalm/"
                                    "2024-10-18-03-00-00"
                                ),
                                "command_id": "full_backup",
                                "pid": 98765,
                                "status": "completed",
                                "output": "Backup completed successfully\\n",
                                "error": None,
                                "return_code": 0,
                                "start_time": "2024-10-18T03:00:00",
                                "end_time": "2024-10-18T03:15:32",
                                "type": "backup",
                                "args": {"id": "2024-10-18-03-00-00"},
                            },
                            {
                                "id": 1235,
                                "command": (
                                    "mariabackup --backup "
                                    "--target-dir=/var/backups/dbcalm/"
                                    "2024-10-18-09-00-00 "
                                    "--incremental-basedir=/var/backups/dbcalm/"
                                    "2024-10-18-03-00-00"
                                ),
                                "command_id": "incremental_backup",
                                "pid": 98766,
                                "status": "running",
                                "output": "Starting incremental backup...\\n",
                                "error": None,
                                "return_code": None,
                                "start_time": "2024-10-18T09:00:00",
                                "end_time": None,
                                "type": "backup",
                                "args": {
                                    "id": "2024-10-18-09-00-00",
                                    "from_backup_id": "2024-10-18-03-00-00",
                                },
                            },
                        ],
                        "pagination": {
                            "total": 156,
                            "page": 1,
                            "per_page": 25,
                            "total_pages": 7,
                        },
                    },
                },
            },
        },
    },
)
async def list_processes(
    _: Annotated[dict, Depends(verify_token)],
    query: Annotated[
        str | None,
        Query(
            description=(
                "Filter processes using format 'field|value' or "
                "'field|operator|value'. "
                "Operators: eq, ne, gt, gte, lt, lte, in, nin. "
                f"Valid fields: {', '.join([f.value for f in ProcessQueryField])}"
            ),
            openapi_examples={
                "by_status": {
                    "summary": "Filter by status",
                    "value": "status|completed",
                },
                "by_type": {
                    "summary": "Filter by type",
                    "value": "type|backup",
                },
                "by_date_range": {
                    "summary": "Filter by start time",
                    "value": "start_time|gte|2024-10-01T00:00:00",
                },
            },
        ),
    ] = None,
    order: Annotated[
        str | None,
        Query(
            description=(
                "Order results using format 'field|direction'. "
                f"Valid fields: {', '.join([f.value for f in ProcessOrderField])}. "
                "Direction: asc or desc"
            ),
            openapi_examples={
                "newest_first": {
                    "summary": "Newest first",
                    "value": "start_time|desc",
                },
                "by_status": {
                    "summary": "Order by status",
                    "value": "status|asc",
                },
            },
        ),
    ] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=1000)] = 25,
) -> ProcessListResponse:
    repository = ProcessRepository()
    query_filters = parse_query_with_operators(query)
    order_filters = parse_query_with_operators(order)

    # Validate field names using enums
    valid_query_fields = {f.value for f in ProcessQueryField}
    for f in query_filters:
        if f.field not in valid_query_fields:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid query field: {f.field}. "
                    f"Valid fields: {', '.join(valid_query_fields)}"
                ),
            )

    valid_order_fields = {f.value for f in ProcessOrderField}
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

    return ProcessListResponse(
        items=[ProcessResponse(**item.model_dump()) for item in items],
        pagination=PaginationInfo(
            total=total,
            page=page,
            per_page=per_page,
            total_pages=(total + per_page - 1) // per_page,
        ),
    )
