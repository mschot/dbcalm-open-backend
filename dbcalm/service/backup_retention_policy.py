from datetime import UTC, datetime, timedelta

from dbcalm.data.model.backup import Backup
from dbcalm.data.model.schedule import Schedule
from dbcalm.data.repository.backup import BackupRepository
from dbcalm.data.repository.schedule import ScheduleRepository
from dbcalm.logger.logger_factory import logger_factory


class BackupRetentionPolicy:
    """Service for evaluating backup retention policies.

    Encapsulates business logic for determining which backups should be deleted
    based on schedule retention policies and backup chain relationships.
    """

    def __init__(self, backup_repository: BackupRepository) -> None:
        self.backup_repo = backup_repository
        self.logger = logger_factory()

    def _convert_retention_to_days(self, value: int, unit: str) -> int:
        """Convert retention period to days."""
        if unit == "days":
            return value
        if unit == "weeks":
            return value * 7
        if unit == "months":
            return value * 30
        msg = f"Unknown retention unit: {unit}"
        raise ValueError(msg)

    def _get_retention_cutoff_date(self, schedule: Schedule) -> datetime | None:
        """Get the cutoff date for backup retention."""
        if schedule.retention_value is None or schedule.retention_unit is None:
            return None

        days = self._convert_retention_to_days(
            schedule.retention_value,
            schedule.retention_unit,
        )
        return datetime.now(tz=UTC) - timedelta(days=days)

    def _identify_backup_chains(self, backups: list[Backup]) -> list[list[Backup]]:
        """Group backups into chains.

        A chain starts with a full backup (from_backup_id is None)
        and includes all incrementals until the next full backup.
        """
        chains = []
        current_chain = []

        for backup in backups:
            if backup.from_backup_id is None:
                # Start of a new chain (full backup)
                if current_chain:
                    chains.append(current_chain)
                current_chain = [backup]
            else:
                # Incremental backup - add to current chain
                current_chain.append(backup)

        # Don't forget the last chain
        if current_chain:
            chains.append(current_chain)

        return chains

    def _is_chain_expired(
        self,
        chain: list[Backup],
        cutoff_date: datetime,
    ) -> bool:
        """Check if ALL backups in a chain are older than the cutoff date."""
        if not chain:
            return False

        # Ensure start_time is timezone-aware (add UTC if naive)
        for backup in chain:
            if backup.start_time.tzinfo is None:
                backup.start_time = backup.start_time.replace(tzinfo=UTC)

        return all(backup.start_time < cutoff_date for backup in chain)

    def _get_expired_backups_for_schedule(
        self,
        schedule: Schedule,
    ) -> list[Backup]:
        """Get list of backups to delete for a specific schedule.

        Args:
            schedule: Schedule with retention policy

        Returns:
            List of Backup objects that should be deleted
        """
        if schedule.retention_value is None or schedule.retention_unit is None:
            return []

        cutoff_date = self._get_retention_cutoff_date(schedule)
        if cutoff_date is None:
            return []

        # Get backups from repository
        from dbcalm.util.parse_query_with_operators import (  # noqa: PLC0415
            QueryFilter,
        )

        query = [
            QueryFilter(field="schedule_id", operator="eq", value=str(schedule.id)),
        ]
        order = [QueryFilter(field="start_time", operator="eq", value="asc")]

        backups, _ = self.backup_repo.get_list(
            query=query,
            order=order,
            page=None,
            per_page=None,
        )

        # Evaluate retention policy
        chains = self._identify_backup_chains(backups)

        backups_to_delete = []
        for chain in chains:
            if self._is_chain_expired(chain, cutoff_date):
                backups_to_delete.extend(chain)

        return backups_to_delete

    def get_expired_backups(self, schedule_id: int | None = None) -> list[Backup]:
        """Get list of backups that should be deleted based on retention policies.

        Args:
            schedule_id: Optional schedule ID to evaluate.
                If None, evaluates all schedules.

        Returns:
            List of Backup objects that should be deleted according to
            retention policies
        """
        schedule_repo = ScheduleRepository()

        if schedule_id is not None:
            # Get backups for specific schedule
            schedule = schedule_repo.get(schedule_id)
            if not schedule:
                self.logger.warning("Schedule %d not found", schedule_id)
                return []

            return self._get_expired_backups_for_schedule(schedule)

        # Get all schedules and process each one
        schedules, _ = schedule_repo.get_list(
            query=None,
            order=None,
            page=None,
            per_page=None,
        )

        all_backups_to_delete = []
        for schedule in schedules:
            expired_backups = self._get_expired_backups_for_schedule(schedule)
            all_backups_to_delete.extend(expired_backups)

        return all_backups_to_delete
