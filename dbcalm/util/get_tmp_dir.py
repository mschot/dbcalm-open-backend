import uuid
from pathlib import Path


def get_tmp_dir(backup_dir: str) -> str:
    tmp_dir = backup_dir + "/tmp/" + str(uuid.uuid4())  # noqa: S108
    path = Path(tmp_dir)
    path.mkdir(parents=True, exist_ok=True)
    return tmp_dir
