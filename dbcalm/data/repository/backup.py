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
        required_backups = [backup.id]
        current = backup
        while current.from_backup_id:
            prev_backup = BackupRepository().get(current.from_backup_id)
            if prev_backup:
                required_backups.append(prev_backup.id)
                current = prev_backup
            else:
                msg = f"Backup with id {current.from_backup_id} not found"
                raise NotFoundError(msg)

        required_backups.reverse()
        return required_backups

    def latest_backup(self) -> Backup | None:
        # get list of backups ordered by end_time desc
        # and limit 1 and return the first item
        try:
            backup = self.adapter.get_list(Backup, {}, {"end_time": "desc"}, 1, 1)[0][0]
        except (IndexError, TypeError):
            backup = None
        
        return backup
        
