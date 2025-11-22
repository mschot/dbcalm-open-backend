
import shutil
import threading
from pathlib import Path
from queue import Queue

from dbcalm.config.config_factory import config_factory
from dbcalm.data.data_types.enum_types import RestoreTarget
from dbcalm.data.model.process import Process
from dbcalm.data.repository.backup import BackupRepository
from dbcalm.data.repository.restore import RestoreRepository
from dbcalm.data.transformer.process_to_backup import process_to_backup
from dbcalm.data.transformer.process_to_restore import process_to_restore
from dbcalm.logger.logger_factory import logger_factory


class ProcessQueueHandler:
    def __init__(self, queue: Queue) -> None:
        self.queue = queue
        self.logger = logger_factory()
        self.config = config_factory()
        self.backup_repo = BackupRepository()
        self.restore_repo = RestoreRepository()

    def handle(self) -> None:
        while True:
            process = self.queue.get(block=True) # type: Process
            self.queue.task_done()

            if process.return_code != 0:
                self.logger.error(
                    "Process %d failed with return code %d",
                    process.pid, process.return_code,
                )

                self.logger.error(process.error)
                self.cleanup(process)
                continue

            if process.type == "backup":
                backup = process_to_backup(process)
                self.backup_repo.create(backup)
                self.logger.debug("Backup %s created", backup.id)
            elif process.type == "restore":
                restore = process_to_restore(process)
                self.restore_repo.create(restore)
                self.logger.debug("Restore %s created", restore.id)

                # Clean up tmp folder for database restores in background
                if restore.target == RestoreTarget.DATABASE:
                    threading.Thread(
                        target=self.remove_tmp_restore_folder,
                        args=(restore.target_path,),
                        daemon=True,
                    ).start()
            elif process.type == "cleanup_backups":
                self.process_cleanup_backups(process)

    def cleanup(self, process: Process) -> None:

        if (
            process.type == "backup" and hasattr(process, "args")
            and process.args.get("id")
        ):
            self.remove_backup_folder(process.args.get("id"))
        elif process.type == "cleanup_backups":
            # Handle partial failures - delete records for folders that were deleted
            self.process_cleanup_backups(process)

    def remove_backup_folder(self, id: str) -> None:
        # do cleanup of backup folder in case it was created but not completed
        backup_dir = self.config.value("backup_dir").rstrip("/")
        backup_path = Path(f"{backup_dir}/{id}")
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

    def remove_tmp_restore_folder(self, tmp_path: str) -> None:
        # Clean up tmp folder after successful database restore
        restore_path = Path(tmp_path)
        if restore_path.exists():
            try:
                shutil.rmtree(restore_path)
                self.logger.debug(
                    "Cleaned up tmp restore folder: %s",
                    restore_path,
                )
            except Exception:
                self.logger.exception(
                    "Failed to cleanup tmp restore folder %s",
                    restore_path,
                )

    def process_cleanup_backups(self, process: Process) -> None:
        """Process cleanup_backups command - delete backup records for deleted folders.

        After the command service deletes backup folders, this method:
        - Checks which folders were actually deleted
        - Deletes the corresponding backup records from the database
        - Only deletes records if the folder no longer exists

        This follows the same pattern for both success and failure:
        - On success: folders should be deleted, remove all records
        - On failure: some folders may still exist, only remove records for
          deleted folders
        """
        if not hasattr(process, "args") or not process.args:
            self.logger.warning("cleanup_backups process has no args")
            return

        backup_ids = process.args.get("backup_ids", [])
        if not backup_ids:
            self.logger.warning("cleanup_backups process has no backup_ids")
            return

        backup_dir = self.config.value("backup_dir").rstrip("/")
        records_deleted = 0

        for backup_id in backup_ids:
            folder_path = Path(f"{backup_dir}/{backup_id}")

            # Only delete the record if the folder no longer exists
            if not folder_path.exists():
                try:
                    if self.backup_repo.delete(backup_id):
                        records_deleted += 1
                        self.logger.debug(
                            "Deleted backup record %s (folder no longer exists)",
                            backup_id,
                        )
                except Exception:
                    self.logger.exception(
                        "Failed to delete backup record %s from database",
                        backup_id,
                    )
            else:
                self.logger.warning(
                    "Backup folder %s still exists, keeping record",
                    folder_path,
                )

        self.logger.info(
            "Cleanup complete: deleted %d backup records out of %d",
            records_deleted,
            len(backup_ids),
        )
