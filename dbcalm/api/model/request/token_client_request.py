from typing import Literal

from pydantic import BaseModel, Field


class TokenClientRequest(BaseModel):
    """OAuth2 token request using client credentials grant type."""

    grant_type: Literal["client_credentials"] = Field(
        description="OAuth2 grant type (must be 'client_credentials')",
    )
    client_id: str = Field(description="Client identifier")
    client_secret: str = Field(description="Client secret")
