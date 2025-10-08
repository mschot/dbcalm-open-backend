from datetime import UTC, datetime

from dbcalm.data.adapter.adapter_factory import adapter_factory
from dbcalm.data.model.schedule import Schedule


class ScheduleRepository:
    def __init__(self) -> None:
        self.adapter = adapter_factory()

    def create(self, schedule: Schedule) -> Schedule:
        schedule.created_at = datetime.now(tz=UTC)
        schedule.updated_at = datetime.now(tz=UTC)
        return self.adapter.create(schedule)

    def get(self, schedule_id: int) -> Schedule | None:
        return self.adapter.get(Schedule, {"id": str(schedule_id)})

    def get_list(
        self,
        query: list | None = None,
        order: list | None = None,
        page: int | None = 1,
        per_page: int | None = 25,
    ) -> tuple[list[Schedule], int]:
        return self.adapter.get_list(Schedule, query, order, page, per_page)

    def update(self, schedule: Schedule) -> bool:
        schedule.updated_at = datetime.now(tz=UTC)
        return self.adapter.update(schedule)

    def delete(self, schedule_id: int) -> bool:
        return self.adapter.delete(Schedule, {"id": str(schedule_id)})
