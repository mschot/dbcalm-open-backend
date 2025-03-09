from dbcalm.data.adapter.adapter_factory import (
    adapter_factory as data_adapter_factory,
)
from dbcalm.data.model.backup import Backup
from dbcalm.data.model.process import Process


def process_to_backup(process: Process) -> Backup:
    if process.type != "backup":
        msg = "Process type must be 'backup'"
        raise ValueError(msg)

    if not process.args.get("id"):
        msg = "Process must have an id"
        raise ValueError(msg)

    id = process.args.get("id")
    if data_adapter_factory().get(Backup, {"id": id}):
        msg = f"Backup with id {id} already exists and has to be unique"
        raise ValueError(msg)

    from_backup_id = None
    if process.args.get("from_backup_id"):
        from_backup_id = process.args.get("from_backup_id")

    return Backup(
        id=process.args.get("id"),
        from_backup_id=from_backup_id,
        start_time=process.start_time,
        end_time=process.end_time,
        process_id=process.id,
    )
