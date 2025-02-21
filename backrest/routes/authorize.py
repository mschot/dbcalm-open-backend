import time
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from passlib.context import CryptContext

from backrest.data.model.auth_code import AuthCode
from backrest.data.repository.auth_code import AuthCodeRepository
from backrest.data.repository.user import UserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


router = APIRouter()
@router.get("/authorize")
async def authorize(
    redirect_uri: Annotated[str, Query()] = ...,
    state: Annotated[str | None, Query()] = None,
    username: Annotated[str, Query()] = ...,
    password: Annotated[str, Query()] = ...,
) -> dict:
    user = UserRepository().get(username)
    if not user or not pwd_context.verify(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    code = f"authcode_{int(time.time())}"
    # need to store authcode with 10min expiry
    auth_code = AuthCode(
        code=code,
        username=username,
        scopes=["*"],
        expires_at=int(time.time() + 600),
    )
    AuthCodeRepository().create(auth_code)
    return {"redirect": f"{redirect_uri}?code={auth_code.code}&state={state}"}
