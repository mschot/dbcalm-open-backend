import time
from typing import Annotated

import jwt
from fastapi import APIRouter, Body, HTTPException
from passlib.context import CryptContext
from pydantic import Field

from dbcalm.api.model.request.token_auth_code_request import TokenAuthCodeRequest
from dbcalm.api.model.request.token_client_request import TokenClientRequest
from dbcalm.api.model.response.token_response import TokenResponse
from dbcalm.config.config_factory import config_factory
from dbcalm.data.repository.auth_code import AuthCodeRepository
from dbcalm.data.repository.client import ClientRepository

router = APIRouter()
secret_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post(
    "/token",
    responses={
        200: {
            "description": "Token issued successfully",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": (
                            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
                            "eyJzdWIiOiJjbGllbnRfYTFiMmMzZDRlNWY2IiwiZXhwIjox"
                            "NzI5MjM4MTY3LCJzY29wZXMiOlsiKiJdfQ."
                            "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
                        ),
                        "token_type": "bearer",
                    },
                },
            },
        },
    },
)
async def issue_token(
    request_data: Annotated[
        TokenClientRequest | TokenAuthCodeRequest,
        Body(
            description="Token request - use appropriate grant type",
            openapi_examples={
                "client_credentials": {
                    "summary": "Client Credentials Grant",
                    "description": "Use for machine-to-machine authentication",
                    "value": {
                        "grant_type": "client_credentials",
                        "client_id": "your-client-id",
                        "client_secret": "your-client-secret",
                    },
                },
                "authorization_code": {
                    "summary": "Authorization Code Grant",
                    "description": (
                        "Use for user authentication via authorization code"
                    ),
                    "value": {
                        "grant_type": "authorization_code",
                        "code": "authcode_1234567890",
                    },
                },
            },
        ),
        Field(discriminator="grant_type"),
    ],
) -> TokenResponse:
    client_repo = ClientRepository()
    config = config_factory()
    jwt_secret_key = config.value("jwt_secret_key")
    jwt_algorithm = config.value("jwt_algorithm", default="HS256")

    if request_data.grant_type == "client_credentials":
        client = client_repo.get(request_data.client_id)
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
