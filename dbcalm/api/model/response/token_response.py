from dbcalm.api.model.response.base_response import BaseResponse


class TokenResponse(BaseResponse):
    access_token: str
    token_type: str
