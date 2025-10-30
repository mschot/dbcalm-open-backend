
import os
import re
import subprocess
import sys

from packaging.version import Version

from dbcalm.config.config import Config
from dbcalm_mariadb_cmd.builder.mariadb_backup_cmd_builder import (
    MariadbBackupCmdBuilder,
)


def get_clean_env_for_system_binaries() -> dict[str, str]:
    """Get environment for system binaries when running from PyInstaller.

    When running as a PyInstaller bundle, clear the bundled library path
    and use system libraries instead. This prevents conflicts when executing
    system binaries like mariabackup, mysqladmin, etc.
    """
    env = os.environ.copy()

    # If running from PyInstaller bundle, use system libraries
    if getattr(sys, "frozen", False):
        # Clear the PyInstaller library path
        env.pop("LD_LIBRARY_PATH", None)
        # Use system library paths
        env["LD_LIBRARY_PATH"] = "/usr/lib/x86_64-linux-gnu:/usr/lib:/lib"

    return env


def server_version() -> Version:
    version = None
    response = subprocess.run(
        ["/usr/bin/mariadb-admin", "--version"],
        shell=False,
        capture_output=True,
        text=True,
        check=True,
        env=get_clean_env_for_system_binaries(),
    )
    if response.returncode == 0:
        # Look for a substring that matches major.minor.patch-MariaDB
        match = re.search(r"(\d+\.\d+\.\d+)-MariaDB", response.stdout)
        if match:
            version = match.group(1)
    return Version(version)

def mariadb_backup_cmd_builder_factory(config: Config) -> MariadbBackupCmdBuilder:
    return MariadbBackupCmdBuilder(config, server_version())


