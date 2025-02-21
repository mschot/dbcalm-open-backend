from backrest.data.adapter.adapter_factory import adapter_factory
from backrest.data.model.backup import Backup


class BackupRepository:
    def __init__(self) -> None:
        self.adapter = adapter_factory()

    def create(self, backup: Backup) -> None:
        return self.adapter.create(backup)

    def get(self, identifier: str) -> Backup | None:
        return self.adapter.get(Backup, {"identifier": identifier})

    def list(
            self,
            query: dict | None,
            page: int | None = 1,
            per_page: int | None = 100,
    ) -> tuple[list[Backup], int]:
        items, total = self.adapter.list(Backup, query, page, per_page)
        return items, total
