from datetime import UTC, datetime

from dbcalm.config.config_factory import config_factory
from dbcalm.data.model.schedule import Schedule


class CronFileBuilder:
    def __init__(self) -> None:
        self.config = config_factory()

    def generate_cron_expression(self, schedule: Schedule) -> str:
        """Generate cron expression from schedule.

        Cron format: minute hour day_of_month month day_of_week
        """
        minute = str(schedule.minute)
        hour = str(schedule.hour)

        if schedule.frequency == "daily":
            return f"{minute} {hour} * * *"
        elif schedule.frequency == "weekly":
            day_of_week = str(schedule.day_of_week) if schedule.day_of_week is not None else "*"
            return f"{minute} {hour} * * {day_of_week}"
        elif schedule.frequency == "monthly":
            day_of_month = str(schedule.day_of_month) if schedule.day_of_month is not None else "*"
            return f"{minute} {hour} {day_of_month} * *"
        else:
            msg = f"Unknown frequency: {schedule.frequency}"
            raise ValueError(msg)

    def generate_cron_command(self, schedule: Schedule) -> str:
        """Generate the dbcalm backup command that will be executed by cron."""
        # Build command to call dbcalm backup CLI
        cmd = (
            f'/usr/bin/dbcalm backup {schedule.backup_type} '
            f'>> /var/log/{self.config.PROJECT_NAME}/cron-{schedule.id}.log 2>&1'
        )

        return cmd

    def build_cron_file_content(self, schedules: list[Schedule]) -> str:
        """Build complete cron file content from list of schedules.

        Only includes enabled schedules.
        Returns complete file content as string.
        """
        # Filter to only enabled schedules
        enabled_schedules = [s for s in schedules if s.enabled]

        # Build header
        timestamp = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
        lines = [
            "# DBCalm Backup Schedules",
            "# Auto-generated - do not edit manually",
            f"# Last updated: {timestamp}",
            "",
        ]

        # Add each schedule
        for schedule in enabled_schedules:
            cron_expression = self.generate_cron_expression(schedule)
            cron_command = self.generate_cron_command(schedule)

            lines.append(f"# {schedule.title} (ID: {schedule.id})")
            lines.append(f"{cron_expression} root {cron_command}")
            lines.append("")

        return "\n".join(lines)
