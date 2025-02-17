
from datetime import datetime, timezone
from typing import Optional

from backrest.config.yaml_config import Config
from backrest_cmd.builder.backup_cmd_builder import BackupCommandBuilder


class MariadbBackupCmdBuilder(BackupCommandBuilder):
    def __init__(self, config :Config) -> None:
        self.config = config

    def build(
            self,
            identifier: str,
            incremental_base_dir: Optional[str] = None,
        ) -> list:
        command = ["mariabackup"]

        if self.config.value("backup_credentials_file") is not None:
            command.append(f"""--defaults-file=
                           { self.config.value("backup_credentials_file")}""")
        else:
            command.append(
                f"""--defaults-file=
                /etc/{ self.config.PROJECT_NAME }/backup_credentials.cnf""",
            )

       ## Add options for backup
        command.append("--backup")
        command.append(
            f"""--target-dir=
                {self.config.value("backup_dir")}/{identifier}""",
            )

        ## Add host to the command
        if self.config.value("db_host") is None:
            host = "localhost"
        else:
            host = self.config.value("db_host")
        command.append(f"--host={host}")

        ## Add option for incremental backups
        if incremental_base_dir is not None:
            command.append("--incremental-basedir=" + incremental_base_dir)

        ## Add option for stream backups
        stream = self.config.value("stream")
        if stream:
            command.append("--stream=xbstream")

        ## Add option for compression
        compression = self.config.value("compression")
        if compression is None and stream:
                compression = self.default_stream_compression

        match compression:
            case "gzip":
                command.append("| gzip")
            case "zstd":
                # explanation of the command:
                # - = read from stdin
                # -c = write to stdout
                # -T0 = use all available threads
                command.append("| zstd - -c -T0")

        ## Add option to forward to another command (or write to file)
        forward = self.config.value("forward")
        if stream and forward is None:
            timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")
            command.append(
                f"> { self.config.value("backup_dir") }/backup-{ timestamp }.xbstream",
            )

        if forward is not None:
            command.append("| " + forward)

        return command

    def build_full_backup_cmd(self, identifier: str) -> list:
        return self.build(identifier)

    def build_incremental_backup_cmd(
            self,
            identifier: str,
            from_identifier: str,
        ) -> list:
        incremental_base_dir = f"""
            { self.config.value("backup_dir") }/{ from_identifier }
        """
        return self.build(identifier, incremental_base_dir)


