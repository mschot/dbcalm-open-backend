from backrest.data.adapter.adapter_factory import (
    adapter_factory as data_adapter_factory,
)
from backrest.data.model.backup import Backup
from backrest.data.model.process import Process


def process_to_backup(process: Process) -> Backup:
    if process.type != "backup":
        msg = "Process type must be 'backup'"
        raise ValueError(msg)

    if not process.args.get("identifier"):
        msg = "Process must have an identifier"
        raise ValueError(msg)

    identifier = process.args.get("identifier")
    if data_adapter_factory().get(Backup, {"identifier": identifier}):
        msg = f"Backup with identifier {identifier} already exists and has to be unique"
        raise ValueError(msg)

    from_identifier = None
    if process.args.get("from_identifier"):
        from_identifier = process.args.get("from_identifier")

    return Backup(
        identifier=process.args.get("identifier"),
        from_identifier=from_identifier,
        start_time=process.start_time,
        end_time=process.end_time,
    )
