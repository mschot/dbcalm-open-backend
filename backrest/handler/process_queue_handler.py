
import shutil
from pathlib import Path
from queue import Queue

from backrest.config.config_factory import config_factory
from backrest.data.adapter.adapter_factory import (
    adapter_factory as data_adapter_factory,
)
from backrest.data.model.process import Process
from backrest.data.transformer.process_to_backup import process_to_backup
from backrest.logger.logger_factory import logger_factory


class ProcessQueueHandler:
    def __init__(self, queue: Queue) -> None:
        self.queue = queue
        self.logger = logger_factory()
        self.config = config_factory()

    def handle(self) -> None:
        while True:
            process = self.queue.get(block=True)
            self.queue.task_done()

            if process.return_code != 0:
                self.logger.error(
                    "Process %d failed with return code %d",
                    process.pid, process.return_code,
                )

                self.cleanup(process)
                continue

            data_adapter = data_adapter_factory()
            if process.type == "backup":
                backup = process_to_backup(process)
                data_adapter.create(backup)
                self.logger.debug("Backup %s created", backup.identifier)
            elif process.type == "restore":
                self.logger.debug("Restore completed successfully")
            break

    def cleanup(self, process: Process) -> None:

        if (
            process.type == "backup" and hasattr(process, "args")
            and process.args.get("identifier")
        ):
            self.remove_backup_folder(process.args.get("identifier"))

    def remove_backup_folder(self, identifier: str) -> None:
        # do cleanup of backup folder in case it was created but not completed
        backup_path = Path(
            f"{self.config.value("backup_dir").rstrip("/")}/{identifier}",
        )
        if backup_path.exists():
            try:
                shutil.rmtree(backup_path)
                self.logger.debug(
                    "Cleaned up incomplete backup folder: %s",
                    backup_path,
                )
            except Exception:
                self.logger.exception(
                    "Failed to cleanup backup folder %s",
                    backup_path,
                )
