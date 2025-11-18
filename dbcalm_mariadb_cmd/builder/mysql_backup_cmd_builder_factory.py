import re
import subprocess

from packaging.version import Version

from dbcalm.config.config import Config
from dbcalm_mariadb_cmd.builder.mariadb_backup_cmd_builder_factory import (
    get_clean_env_for_system_binaries,
)
from dbcalm_mariadb_cmd.builder.mysql_backup_cmd_builder import (
    MysqlBackupCmdBuilder,
)


def server_version() -> Version:
    """Get MySQL server version from mysqladmin.

    Returns:
        Version: MySQL server version (e.g., 8.0.35)
    """
    version = None
    response = subprocess.run(
        ["/usr/bin/mysqladmin", "--version"],
        shell=False,
        capture_output=True,
        text=True,
        check=True,
        env=get_clean_env_for_system_binaries(),
    )
    if response.returncode == 0:
        # Look for version pattern like "mysqladmin  Ver 8.0.35 for Linux"
        # or "Ver 8.0.35-0ubuntu0.22.04.1 for Linux"
        match = re.search(r"Ver (\d+\.\d+\.\d+)", response.stdout)
        if match:
            version = match.group(1)
    return Version(version)


def mysql_backup_cmd_builder_factory(config: Config) -> MysqlBackupCmdBuilder:
    """Create MySQL backup command builder with server version detection.

    Args:
        config: Application configuration

    Returns:
        MysqlBackupCmdBuilder: Configured builder instance
    """
    return MysqlBackupCmdBuilder(config, server_version())
