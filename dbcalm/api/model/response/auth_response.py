from pydantic import Field

from dbcalm.api.model.response.base_response import BaseResponse


class AuthCodeResponse(BaseResponse):
    """Response model for authorization endpoint."""

    code: str = Field(description="Authorization code for token exchange")
