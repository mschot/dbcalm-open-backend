from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from backrest.auth.verify_token import verify_token
from backrest.data.repository.client import ClientRepository
from backrest.util.parse_query_dict import parse_query_dict

router = APIRouter()
@router.get("/clients")
async def list_clients(
    _: Annotated[dict, Depends(verify_token)],
    query: str | None = None,
    order: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=1000)] = 25,
) -> dict[str, Any]:
    repository = ClientRepository()
    query_dict = parse_query_dict(query)
    order_dict = parse_query_dict(order)
    items, total = repository.list(query_dict, order_dict, page=page, per_page=per_page)

    return {
        "items": [item.model_dump(exclude={"secret"}) for item in items],
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
        },
    }
