import logging

from dbcalm.config.config_factory import config_factory
from dbcalm.config.validator import ValidatorError
from dbcalm.logger.file_logger import FileLogger


def logger_factory() -> logging.Logger:
    config = config_factory()

    if config.value("log") is None or config.value("log")  == "file":
        return FileLogger().get_logger()

    msg = "Unknown logger type"
    raise ValidatorError(msg)

