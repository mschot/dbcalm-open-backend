import time  # noqa: A005

import jwt
from fastapi import APIRouter, HTTPException
from passlib.context import CryptContext

from dbcalm.api.model.request.token_auth_code_request import TokenAuthCodeRequest
from dbcalm.api.model.request.token_client_request import TokenClientRequest
from dbcalm.api.model.response.token_response import TokenResponse
from dbcalm.config.config_factory import config_factory
from dbcalm.data.adapter.adapter_factory import (
    adapter_factory as data_adapter_factory,
)
from dbcalm.data.model.client import Client
from dbcalm.data.repository.auth_code import AuthCodeRepository

router = APIRouter()
secret_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/token")
async def issue_token(
    request_data: TokenClientRequest | TokenAuthCodeRequest,
) -> TokenResponse:
    adapter = data_adapter_factory()
    config = config_factory()
    jwt_secret_key = config.value("jwt_secret_key")
    jwt_algorithm = config.value("jwt_algorithm")

    if request_data.grant_type == "client_credentials":
        client = adapter.get(Client, {"id":request_data.client_id})
        if not client or not secret_context.verify(
            request_data.client_secret,
            client.secret,
        ):
            raise HTTPException(status_code=400, detail="Invalid client credentials")

        payload = {
            "sub": client.id,
            "exp": time.time() + 3600,
            "scopes": client.scopes,
        }
        token = jwt.encode(payload, jwt_secret_key, algorithm=jwt_algorithm)
        return {"access_token": token, "token_type": "bearer"}

    if request_data.grant_type == "authorization_code":
        auth_data = AuthCodeRepository().get(request_data.code)
        if not auth_data:
            raise HTTPException(status_code=400, detail="Invalid authorization code")

        payload = {
            "sub": auth_data.username,
            "exp": time.time() + 3600,
            "scopes": auth_data.scopes,
        }
        token = jwt.encode(payload, jwt_secret_key, algorithm=jwt_algorithm)
        return {"access_token": token, "token_type": "bearer"}

    raise HTTPException(status_code=400, detail="Unsupported grant type")
