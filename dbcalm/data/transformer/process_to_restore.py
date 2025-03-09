from dbcalm.data.adapter.adapter_factory import (
    adapter_factory as data_adapter_factory,
)
from dbcalm.data.model.backup import Backup
from dbcalm.data.model.process import Process
from dbcalm.data.model.restore import Restore, RestoreBackupLink


def process_to_restore(process: Process) -> Restore:
    if process.type != "restore":
        msg = "Process type must be 'restore'"
        raise ValueError(msg)

    if not process.args.get("id"):
        msg = "Process must have an id"
        raise ValueError(msg)

    id = process.args.get("id")
    if data_adapter_factory().get(Restore, {"id": id}):
        msg = f"Restore with id {id} already exists and has to be unique"
        raise ValueError(msg)

    # Create restore
    restore = Restore(
        id=process.args.get("id"),
        start_time=process.start_time,
        end_time=process.end_time,
        target=process.args.get("target"),
        target_path=process.args.get("target_path"),
    )

    # Get backup IDs from process args and link them
    if process.args.get("backup_ids"):
        backup_ids = process.args.get("backup_ids").split(",")
        for backup_id in backup_ids:
            backup = data_adapter_factory().get(Backup, {"id": backup_id})
            if backup:
                link = RestoreBackupLink(restore_id=restore.id, backup_id=backup.id)
                data_adapter_factory().create(link)

    return restore
