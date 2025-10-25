from pydantic import Field

from dbcalm.api.model.response.base_response import BaseResponse
from dbcalm.api.model.response.list_response import PaginationInfo


class ClientResponse(BaseResponse):
    """Response model for a single client."""

    id: str = Field(description="Unique client identifier")
    label: str = Field(description="Human-readable label for the client")
    scopes: list[str] = Field(description="List of OAuth2 scopes granted to the client")


class ClientWithSecretResponse(BaseResponse):
    """Response model for client creation (includes secret)."""

    id: str = Field(description="Unique client identifier")
    secret: str = Field(description="Client secret (only shown once at creation)")
    label: str = Field(description="Human-readable label for the client")
    scopes: list[str] = Field(description="List of OAuth2 scopes granted to the client")


class ClientListResponse(BaseResponse):
    """Response model for paginated list of clients."""

    items: list[ClientResponse] = Field(
        description="List of clients (secrets excluded)",
    )
    pagination: PaginationInfo = Field(description="Pagination metadata")
