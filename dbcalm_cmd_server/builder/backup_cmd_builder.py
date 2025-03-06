
from abc import ABC, abstractmethod

from dbcalm.data.types.enum_types import RestoreTarget


class BackupCommandBuilder(ABC):
    @abstractmethod
    def build_full_backup_cmd(self: str) -> list:
        pass

    @abstractmethod
    def build_incremental_backup_cmd(self: str, from_identifier: str) -> list:
        pass

    @abstractmethod
    def build_restore_cmds(
            self: str,
            tmp_dir : str,
            identifier_list: list,
            target: RestoreTarget,
        ) -> list:
        pass


