
import re
import subprocess

from packaging.version import Version

from dbcalm.config.config import Config
from dbcalm_cmd_server.builder.mariadb_backup_cmd_builder import MariadbBackupCmdBuilder


def server_version() -> Version:
    version = None
    response = subprocess.run(  # noqa: S603
        ["/usr/bin/mariadb-admin", "--version"],
        shell=False,
        capture_output=True,
        text=True,
        check=True,
    )
    if response.returncode == 0:
        # Look for a substring that matches major.minor.patch-MariaDB
        match = re.search(r"(\d+\.\d+\.\d+)-MariaDB", response.stdout)
        if match:
            version = match.group(1)
    return Version(version)

def mariadb_backup_cmd_builder_factory(config: Config) -> MariadbBackupCmdBuilder:
    return MariadbBackupCmdBuilder(config, server_version())


