from datetime import UTC, datetime
from pathlib import Path


def get_tmp_dir(backup_dir: str, subdirectory: str = "tmp") -> str:
    timestamp = datetime.now(tz=UTC).strftime("%Y-%m-%d-%H-%M-%S")
    tmp_dir = backup_dir + f"/{subdirectory}/" + timestamp
    path = Path(tmp_dir)
    path.mkdir(parents=True, exist_ok=True)
    return tmp_dir
