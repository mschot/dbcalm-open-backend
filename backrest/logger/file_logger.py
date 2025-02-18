import logging
from pathlib import Path

from backrest.config.config_factory import config_factory


class FileLogger:

    def __init__(self) -> None:
        self.config = config_factory()
        self.logger = logging.getLogger(self.config.PROJECT_NAME)

        # Determine log file location
        log_file = f"/var/log/{self.config.PROJECT_NAME}/{self.config.PROJECT_NAME}.log"
        if self.config.value("log_file") is not None:
            log_file = self.config.value("log_file")

        log_file_path = Path(log_file)
        # Ensure the log directory exists
        log_dir = log_file_path.parent
        try:
            if not Path.exists(log_dir):
                log_dir.mkdir(exist_ok=True)
        except PermissionError:
            self.logger.exception(
                "Error creating log directory, please create %s manually",
                log_dir,
            )

        # Create file handler
        file_handler = logging.FileHandler(log_file)

        # Determine log level
        log_level = logging.DEBUG
        if self.config.value("log_level") is not None:
            try:
                config_log_level = self.config.value("log_level").upper()
                log_level = logging.getLevelNamesMapping()[config_log_level]
            except KeyError:
                msg = f"Invalid log level: {self.config.value('log_level')}"
                raise SystemExit(msg) from KeyError

        file_handler.setLevel(log_level)

        # Set log format
        formatter = logging.Formatter("{asctime} - {levelname} - {message}", style="{")
        file_handler.setFormatter(formatter)
        # Add handler to logger
        self.logger.addHandler(file_handler)

    def get_logger(self) -> logging.Logger:
        """Returns the configured logger instance."""
        return self.logger
