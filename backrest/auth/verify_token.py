import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from backrest.config.config_factory import config_factory

# OAuth2 scheme for receiving tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_token(token: str = Depends(oauth2_scheme)) -> dict:
    config = config_factory()
    jwt_algorithm  = config.value("jwt_algorithm")
    jwt_secret_key = config.value("jwt_secret_key")

    try:
        return jwt.decode(token, jwt_secret_key, algorithms=[jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expired",
        ) from jwt.ExpiredSignatureError
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        ) from jwt.InvalidTokenError
