from pydantic import BaseModel, Field


class DeleteResponse(BaseModel):
    """Generic response for successful deletion."""

    message: str = Field(description="Confirmation message")
