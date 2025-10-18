import time
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel

from dbcalm.api.model.response.auth_response import AuthCodeResponse
from dbcalm.data.model.auth_code import AuthCode
from dbcalm.data.repository.auth_code import AuthCodeRepository
from dbcalm.data.repository.user import UserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserLogin(BaseModel):
    username: str
    password: str

router = APIRouter()
@router.post(
    "/authorize",
    responses={
        200: {
            "description": "Authorization successful",
            "content": {
                "application/json": {
                    "example": {
                        "code": "authcode_1729234567",
                    },
                },
            },
        },
    },
)
async def authorize(
    user_login: Annotated[
        UserLogin,
        Body(
            openapi_examples={
                "user_login": {
                    "summary": "User login",
                    "description": (
                        "Authenticate with username and password "
                        "to get authorization code"
                    ),
                    "value": {
                        "username": "admin",
                        "password": "your-secure-password",
                    },
                },
            },
        ),
    ],
) -> AuthCodeResponse:

    user = UserRepository().get(user_login.username)
    if not user or not pwd_context.verify(user_login.password, user.password):
        raise HTTPException(
            status_code=401,
            detail="Username and/or password did not match",
        )

    code = f"authcode_{int(time.time())}"
    # need to store authcode with 10min expiry
    auth_code = AuthCode(
        code=code,
        username=user.username,
        scopes=["*"],
        expires_at=int(time.time() + 600),
    )
    AuthCodeRepository().create(auth_code)
    return AuthCodeResponse(code=auth_code.code)
