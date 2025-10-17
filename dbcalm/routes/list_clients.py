from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from dbcalm.api.model.query.client_query import (
    ClientOrderField,
    ClientQueryField,
)
from dbcalm.api.model.response.client_response import (
    ClientListResponse,
    ClientResponse,
)
from dbcalm.api.model.response.list_response import PaginationInfo
from dbcalm.auth.verify_token import verify_token
from dbcalm.data.repository.client import ClientRepository
from dbcalm.util.parse_query_with_operators import parse_query_with_operators

router = APIRouter()
@router.get("/clients")
async def list_clients(
    _: Annotated[dict, Depends(verify_token)],
    query: Annotated[
        str | None,
        Query(
            description=(
                "Filter clients using format 'field|value' or "
                "'field|operator|value'. "
                "Operators: eq, ne, gt, gte, lt, lte, in, nin. "
                f"Valid fields: {', '.join([f.value for f in ClientQueryField])}"
            ),
            openapi_examples={
                "by_id": {
                    "summary": "Filter by ID",
                    "value": "id|my-client",
                },
                "by_label": {
                    "summary": "Filter by label",
                    "value": "label|Production Client",
                },
            },
        ),
    ] = None,
    order: Annotated[
        str | None,
        Query(
            description=(
                "Order results using format 'field|direction'. "
                f"Valid fields: {', '.join([f.value for f in ClientOrderField])}. "
                "Direction: asc or desc"
            ),
            openapi_examples={
                "by_id": {
                    "summary": "Order by ID",
                    "value": "id|asc",
                },
                "by_label": {
                    "summary": "Order by label",
                    "value": "label|asc",
                },
            },
        ),
    ] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=1000)] = 25,
) -> ClientListResponse:
    repository = ClientRepository()
    query_filters = parse_query_with_operators(query)
    order_filters = parse_query_with_operators(order)

    # Validate field names using enums
    valid_query_fields = {f.value for f in ClientQueryField}
    for f in query_filters:
        if f.field not in valid_query_fields:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid query field: {f.field}. "
                    f"Valid fields: {', '.join(valid_query_fields)}"
                ),
            )

    valid_order_fields = {f.value for f in ClientOrderField}
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

    return ClientListResponse(
        items=[ClientResponse(**item.model_dump(exclude={"secret"})) for item in items],
        pagination=PaginationInfo(
            total=total,
            page=page,
            per_page=per_page,
            total_pages=(total + per_page - 1) // per_page,
        ),
    )
