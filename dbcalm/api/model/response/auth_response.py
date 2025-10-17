from pydantic import BaseModel, Field


class AuthCodeResponse(BaseModel):
    """Response model for authorization endpoint."""

    code: str = Field(description="Authorization code for token exchange")
