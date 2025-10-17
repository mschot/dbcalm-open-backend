from typing import Literal

from pydantic import BaseModel, Field


class TokenAuthCodeRequest(BaseModel):
    """OAuth2 token request using authorization code grant type."""

    grant_type: Literal["authorization_code"] = Field(
        description="OAuth2 grant type (must be 'authorization_code')",
    )
    code: str = Field(description="Authorization code from /auth/authorize endpoint")
