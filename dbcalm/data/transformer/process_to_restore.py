

from dbcalm.data.model.process import Process
from dbcalm.data.model.restore import Restore


def process_to_restore(process: Process) -> Restore:
    if process.type != "restore":
        msg = "Process type must be 'restore'"
        raise ValueError(msg)

    return Restore(
        start_time=process.start_time,
        end_time=process.end_time,
        target=process.args.get("target"),
        target_path=process.args.get("tmp_dir"),
        backup_id=process.args.get("id_list")[0],
        process_id=process.id,
    )
