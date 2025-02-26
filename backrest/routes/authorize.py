import time

from fastapi import APIRouter, HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel

from backrest.data.model.auth_code import AuthCode
from backrest.data.repository.auth_code import AuthCodeRepository
from backrest.data.repository.user import UserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserLogin(BaseModel):
    username: str
    password: str

router = APIRouter()
@router.post("/authorize")
async def authorize(
    user_login: UserLogin,
) -> dict:

    user = UserRepository().get(user_login.username)
    if not user or not pwd_context.verify(user_login.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    code = f"authcode_{int(time.time())}"
    # need to store authcode with 10min expiry
    auth_code = AuthCode(
        code=code,
        username=user.username,
        scopes=["*"],
        expires_at=int(time.time() + 600),
    )
    AuthCodeRepository().create(auth_code)
    return {"code" : auth_code.code}
