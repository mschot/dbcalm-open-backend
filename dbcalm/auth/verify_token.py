import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from dbcalm.config.config_factory import config_factory

oauth2 = HTTPBearer()


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2),  # noqa: B008
) -> dict:
    token = credentials.credentials
    config = config_factory()
    jwt_algorithm  = config.value("jwt_algorithm", default="HS256")
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
