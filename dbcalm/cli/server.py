import os

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from dbcalm.config.config_factory import config_factory
from dbcalm.config.validator import Validator
from dbcalm.errors.validation_error import ValidationError
from dbcalm.logger.logger_factory import logger_factory
from dbcalm.routes import (
    authorize,
    create_backup,
    create_client,
    create_restore,
    create_schedule,
    delete_client,
    delete_schedule,
    get_schedule,
    list_backups,
    list_clients,
    list_processes,
    list_restores,
    list_schedules,
    status,
    token,
    update_client,
    update_schedule,
)

config = config_factory()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.value("cors_origins"),
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
app.include_router(list_schedules.router, tags=["Schedules"])
app.include_router(get_schedule.router, tags=["Schedules"])
app.include_router(create_schedule.router, tags=["Schedules"])
app.include_router(update_schedule.router, tags=["Schedules"])
app.include_router(delete_schedule.router, tags=["Schedules"])
app.include_router(status.router, tags=["Status"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch all unhandled exceptions and log them"""
    logger = logger_factory()
    logger.exception(f"Unhandled exception on {request.method} {request.url.path}:")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )

def run() -> None:
    """Start the API server"""
    # Initialize logger early so all errors get logged
    logger = logger_factory()

    # Validate configuration and log any errors
    try:
        Validator(config).validate()
    except ValidationError as e:
        logger.exception("Configuration validation failed:")
        raise

    # Configure uvicorn logging to use the same log file
    log_file = config.value("log_file") or f"/var/log/{config.PROJECT_NAME}/{config.PROJECT_NAME}.log"
    log_level = config.value("log_level", "info").lower()

    uvicorn_log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "file": {
                "class": "logging.FileHandler",
                "filename": log_file,
                "formatter": "default",
            },
        },
        "root": {
            "level": log_level.upper(),
            "handlers": ["file"],
        },
        "loggers": {
            "uvicorn": {"level": log_level.upper(), "handlers": ["file"], "propagate": False},
            "uvicorn.error": {"level": log_level.upper(), "handlers": ["file"], "propagate": False},
            "uvicorn.access": {"level": log_level.upper(), "handlers": ["file"], "propagate": False},
        },
    }

    uvicorn_args = {
            "app": app,
            "host": config.value("api_host", "0.0.0.0"),
            "port": config.value("api_port", 8335),
            "log_config": uvicorn_log_config,
        }
    if config.value("ssl_cert") and config.value("ssl_key"):
        ssl_cert = config.value("ssl_cert")
        ssl_key = config.value("ssl_key")

        if not os.access(ssl_cert, os.R_OK) or not os.access(ssl_key, os.R_OK):
            msg = (
                "SSL certificate and/or key file(s) are not"
                f" readable by {config.PROJECT_NAME}"
            )
            logger.error(msg)
            raise ValidationError(msg)

        uvicorn_args["ssl_certfile"] = ssl_cert
        uvicorn_args["ssl_keyfile"] = ssl_key

    try:
        uvicorn.run(**uvicorn_args)
    except Exception:
        logger.exception("Failed to start API server:")
