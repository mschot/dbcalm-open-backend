
from queue import Queue

from backrest.data.adapter.adapter_factory import (
    adapter_factory as data_adapter_factory,
)
from backrest.data.transformer.process_to_backup import process_to_backup
from backrest.logger.logger_factory import logger_factory


class ProcessQueueHandler:
    def __init__(self, queue: Queue) -> None:
        self.queue = queue
        self.logger = logger_factory()

    def handle(self) -> None:
        while True:
            process = self.queue.get(block=True)
            self.queue.task_done()

            if process.return_code != 0:
                self.logger.error(
                    "Process %d failed with return code %d",
                    process.pid, process.return_code,
                )

                #@TODO do cleanup of backup folder in case it was created but
                # not completed the process has the identifier in the args for backups
                continue

            data_adapter = data_adapter_factory()
            if process.type == "backup":
                backup = process_to_backup(process)
                data_adapter.create(backup)
                self.logger.debug("Backup %s created", backup.identifier)
            elif process.type == "restore":
                self.logger.debug("Restore completed successfully")
            break
