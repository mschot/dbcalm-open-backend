from typing import Generic, TypeVar

from pydantic import BaseModel, Field


class PaginationInfo(BaseModel):
    """Pagination metadata for list responses."""

    total: int = Field(description="Total number of items across all pages")
    page: int = Field(description="Current page number (1-indexed)")
    per_page: int = Field(description="Number of items per page")
    total_pages: int = Field(description="Total number of pages")


T = TypeVar("T")


class ListResponse(BaseModel, Generic[T]):
    """Generic paginated list response."""

    items: list[T] = Field(description="List of items for the current page")
    pagination: PaginationInfo = Field(description="Pagination metadata")
