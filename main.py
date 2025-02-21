import os

import uvicorn
from fastapi import FastAPI

from backrest.config.config_factory import config_factory
from backrest.config.validator import Validator, ValidatorError
from backrest.routes import authorize, create_backups, list_backups, status, token

config = config_factory()
Validator(config).validate()

app = FastAPI()

app.include_router(authorize.router, prefix="/auth", tags=["Authentication"])
app.include_router(token.router, prefix="/auth", tags=["Authentication"])
app.include_router(create_backups.router, tags=["Backups"])
app.include_router(list_backups.router, tags=["Backups"])
app.include_router(status.router, tags=["Status"])

if __name__ == "__main__":

    uvicorn_args = {
        "app": app,
        "host": "0.0.0.0",  # noqa: S104
        "port": 8000,
    }
    if config.value("ssl_cert") and config.value("ssl_key"):
        ssl_cert = config.value("ssl_cert")
        ssl_key = config.value("ssl_key")

        if not os.access(ssl_cert, os.R_OK) or not os.access(ssl_key, os.R_OK):
            msg = (
                "SSL certificate and/or key file(s) are not",
                f" readable by {config.PROJECT_NAME}",
            )
            raise ValidatorError(msg)

        uvicorn_args["ssl_certfile"] = ssl_cert
        uvicorn_args["ssl_keyfile"] = ssl_key

    uvicorn.run(**uvicorn_args)

