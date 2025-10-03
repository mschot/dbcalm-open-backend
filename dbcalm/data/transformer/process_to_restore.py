

from dbcalm.data.model.process import Process
from dbcalm.data.model.restore import Restore
from dbcalm.data.repository.backup import BackupRepository


def process_to_restore(process: Process) -> Restore:
    if process.type != "restore":
        msg = "Process type must be 'restore'"
        raise ValueError(msg)

    id_list = process.args.get("id_list")
    backup_id = id_list[0]

    # Get the latest backup timestamp (last in id_list for incremental, or the only one)
    latest_backup_id = id_list[-1]
    backup_timestamp = None
    if latest_backup_id:
        backup = BackupRepository().get(latest_backup_id)
        if backup:
            backup_timestamp = backup.start_time

    return Restore(
        start_time=process.start_time,
        end_time=process.end_time,
        target=process.args.get("target"),
        target_path=process.args.get("tmp_dir"),
        backup_id=backup_id,
        backup_timestamp=backup_timestamp,
        process_id=process.id,
    )
