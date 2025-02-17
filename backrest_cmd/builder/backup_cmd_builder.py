
from abc import ABC, abstractmethod


class BackupCommandBuilder(ABC):
    @abstractmethod
    def build_full_backup_cmd(self: str) -> list:
        pass

    @abstractmethod
    def build_incremental_backup_cmd(self: str, from_identifier: str) -> list:
        pass


