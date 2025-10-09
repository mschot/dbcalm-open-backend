

from packaging.version import Version

from dbcalm.config.yaml_config import Config
from dbcalm.data.data_types.enum_types import RestoreTarget
from dbcalm_mariadb_cmd.builder.backup_cmd_builder import BackupCommandBuilder

APPY_LOG_ONLY_BEFORE_VERSION = Version("10.2")

DEFAULT_MARIA_BIN = "/usr/bin/mariabackup"

class MariadbBackupCmdBuilder(BackupCommandBuilder):
    def __init__(self, config :Config, server_version: Version) -> None:
        self.config = config
        self.server_version = server_version

    def executable(self) -> str:
        if self.config.value("backup_bin") is not None:
            return self.config.value("backup_bin")
        return DEFAULT_MARIA_BIN

    def build(
            self,
            id: str,
            incremental_base_dir: str | None = None,
        ) -> list:
        command = [self.executable()]

        # because mysqladmin only supports group suffixes we use that one so
        # we can use the same credentials file for both mysqladmin and mariadb
        # mysqladmin needs to be used to check  whether its running before restore
        credentials_file = (self.config.value("backup_credentials_file")
                if self.config.value("backup_credentials_file") is not None
                else f"/etc/{ self.config.PROJECT_NAME }/credentials.cnf")

        command.append(f"--defaults-file={ credentials_file }")
        command.append("--defaults-group-suffix=-dbcalm")
        command.append("--backup")

        command.append(
            f"""--target-dir={self.config.value("backup_dir")}/{id}""",
            )

        ## Add host to the command (always localhost - backup requires local filesystem)
        command.append(f"--host={self.config.DB_HOST}")

        ## Add option for incremental backups
        if incremental_base_dir is not None:
            command.append(f"--incremental-basedir={incremental_base_dir}")

        ## Add option for stream backups
        stream = self.config.value("stream")
        if stream:
            command.append("--stream=xbstream")

        ## Add option for compression
        compression = self.config.value("compression")
        if compression is None and stream:
                compression = self.default_stream_compression

        extension = ""
        match compression:
            case "gzip":
                command.append("| gzip")
                extension = ".gz"
            case "zstd":
                # explanation of the command:
                # - = read from stdin
                # -c = write to stdout
                # -T0 = use all available threads
                command.append("| zstd - -c -T0")
                extension = ".zst"

        ## Add option to forward to another command (or write to file)
        forward = self.config.value("forward")
        if stream and forward is None:
            command.append(
                f"> { self.config.value("backup_dir") }/"
                f"backup-{ id }.xbstream{extension}",
            )

        if forward is not None:
            command.append("| " + forward)

        return command

    def build_full_backup_cmd(self, id: str) -> list:
        return self.build(id)

    def build_incremental_backup_cmd(
            self,
            id: str,
            from_backup_id: str,
        ) -> list:
        incremental_base_dir = (
            f"{ self.config.value("backup_dir") }/{ from_backup_id }"
        )
        return self.build(id, incremental_base_dir)


    def build_restore_cmds(
            self,
            tmp_dir : str,
            id_list: list,
            target: RestoreTarget,
        ) -> list:

        command_list = []
        id_list_copy = id_list.copy()
        full_backup_id = id_list_copy.pop(0)
        original_backup_path = f"{self.config.value('backup_dir')}/{full_backup_id}"
        # could do shutil.copytree but that would stop api flow
        #  whereas this will run consecutively using the process
        #  runner (although will not work on windows)
        command_list.append(["/usr/bin/cp",  "-r", original_backup_path, tmp_dir])
        new_backup_path = f"{tmp_dir}/{full_backup_id}"

        command = [self.executable()]
        command.append("--prepare")
        command.append("--target-dir")
        command.append(new_backup_path)
        # Don't close redo log if there are more incremental backups to apply
        if self.server_version < APPY_LOG_ONLY_BEFORE_VERSION \
            and len(id_list) > 0:
                command.append("--apply-log-only")

        command_list.append(command)

        while len(id_list_copy) > 0:
            id = id_list_copy.pop(0)
            incremental_left = len(id_list_copy)
            command = self.build_incremental_restore_cmd(
                new_backup_path,
                id,
                incremental_left,
                self.server_version,
            )
            command_list.append(command)

        if target == RestoreTarget.DATABASE:
            command = [self.executable()]
            command.append("--copy-back")
            command.append("--target-dir")
            command.append(new_backup_path)
            command_list.append(command)

        return command_list


    def build_incremental_restore_cmd(
            self,
            full_backup_path: str,
            id: str,
            incremental_left: int,
            server_version: str,
        ) -> list:
        command = [self.executable()]
        command.append("--prepare")
        command.append("--target-dir")
        command.append(full_backup_path)
        command.append("--incremental-dir")
        command.append(self.config.value("backup_dir") + "/" + id)
        # Don't close redo log if there are more incremental backups to apply
        if server_version < APPY_LOG_ONLY_BEFORE_VERSION and incremental_left > 0:
            command.append("--apply-log-only")

        return command




