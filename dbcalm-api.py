import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dbcalm.config.config_factory import config_factory
from dbcalm.config.validator import Validator
from dbcalm.errors.validation_error import ValidationError
from dbcalm.logger.logger_factory import logger_factory
from dbcalm.routes import (
    authorize,
    create_backup,
    create_client,
    create_restore,
    delete_client,
    list_backups,
    list_clients,
    list_processes,
    list_restores,
    status,
    token,
    update_client,
)

config = config_factory()
Validator(config).validate()

app = FastAPI()

# TODO: move to config  # noqa: FIX002
origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(authorize.router, prefix="/auth", tags=["Authentication"])
app.include_router(token.router, prefix="/auth", tags=["Authentication"])
app.include_router(create_backup.router, tags=["Backups"])
app.include_router(list_backups.router, tags=["Backups"])
app.include_router(list_clients.router, tags=["Clients"])
app.include_router(delete_client.router, tags=["Clients"])
app.include_router(update_client.router, tags=["Clients"])
app.include_router(create_client.router, tags=["Clients"])
app.include_router(create_restore.router, tags=["Backups"])
app.include_router(list_restores.router, tags=["Restores"])
app.include_router(list_processes.router, tags=["Processes"])
app.include_router(status.router, tags=["Status"])

def api_server() -> None:
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
                "SSL certificate and/or key file(s) are not"
                f" readable by {config.PROJECT_NAME}"
            )
            raise ValidationError(msg)

        uvicorn_args["ssl_certfile"] = ssl_cert
        uvicorn_args["ssl_keyfile"] = ssl_key

    uvicorn.run(**uvicorn_args)

if __name__ == "__main__":
    try:
        api_server()
    except Exception:
        logger = logger_factory()
        logger.exception("Failed to start API server:")

