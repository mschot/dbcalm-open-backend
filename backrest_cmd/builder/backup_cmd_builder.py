
from abc import ABC, abstractmethod

class BackupCommandBuilder(ABC):
    @abstractmethod
    def build_full_backup_cmd(identifier: str) -> list:
        pass

    @abstractmethod
    def build_incremental_backup_cmd(identifier: str, from_identifier: str) -> list:
        pass


