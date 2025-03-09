from dbcalm.data.adapter.adapter_factory import adapter_factory
from dbcalm.data.model.backup import Backup
from dbcalm.errors.not_found_error import NotFoundError


class BackupRepository:
    def __init__(self) -> None:
        self.adapter = adapter_factory()

    def create(self, backup: Backup) -> None:
        return self.adapter.create(backup)

    def get(self, id: str) -> Backup | None:
        return self.adapter.get(Backup, {"id": id})

    def get_list(
            self,
            query: dict | None,
            order: dict | None,
            page: int | None = 1,
            per_page: int | None = 10,
    ) -> tuple[list[Backup], int]:
        items, total = self.adapter.get_list(Backup, query, order, page, per_page)
        return items, total

    def required_backups(self, backup: Backup) -> list:
        required_backups = [backup.identifier]
        current = backup
        while current.from_identifier:
            prev_backup = BackupRepository().get(current.from_identifier)
            if prev_backup:
                required_backups.append(prev_backup.identifier)
                current = prev_backup
            else:
                msg = f"Backup with identifier {current.from_identifier} not found"
                raise NotFoundError(msg)

        required_backups.reverse()
        return required_backups
