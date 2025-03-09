from dbcalm.data.adapter.adapter_factory import adapter_factory
from dbcalm.data.model.restore import Restore


class RestoreRepository:
    def __init__(self) -> None:
        self.adapter = adapter_factory()

    def create(self, restore: Restore) -> None:
        return self.adapter.create(restore)

    def get(self, restore_id: int) -> Restore | None:
        return self.adapter.get(Restore, {"id": restore_id})

    def get_list(
            self,
            query: dict | None,
            order: dict | None,
            page: int | None = 1,
            per_page: int | None = 10,
    ) -> tuple[list[Restore], int]:
        items, total = self.adapter.get_list(Restore, query, order, page, per_page)
        return items, total
