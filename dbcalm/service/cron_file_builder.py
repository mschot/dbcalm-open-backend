from datetime import UTC, datetime

from dbcalm.config.config_factory import config_factory
from dbcalm.data.model.schedule import Schedule


class CronFileBuilder:
    def __init__(self) -> None:
        self.config = config_factory()

    def generate_cron_expression(self, schedule: Schedule) -> str:
        """Generate cron expression from schedule.

        Cron format: minute hour day_of_month month day_of_week
        For intervals: */X for minutes, or */X in hour field
        with * in minute field for hours
        For hourly: minute * * * * (run at specified minute every hour)
        """
        if schedule.frequency == "interval":
            if schedule.interval_unit == "minutes":
                # Run every X minutes: */X * * * *
                return f"*/{schedule.interval_value} * * * *"
            if schedule.interval_unit == "hours":
                # Run every X hours: 0 */X * * *
                return f"0 */{schedule.interval_value} * * *"
            msg = f"Unknown interval unit: {schedule.interval_unit}"
            raise ValueError(msg)

        minute = str(schedule.minute)
        hour = str(schedule.hour)

        if schedule.frequency == "hourly":
            # Run once every hour at the specified minute: minute * * * *
            return f"{minute} * * * *"
        if schedule.frequency == "daily":
            return f"{minute} {hour} * * *"
        if schedule.frequency == "weekly":
            day_of_week = (
                str(schedule.day_of_week) if schedule.day_of_week is not None else "*"
            )
            return f"{minute} {hour} * * {day_of_week}"
        if schedule.frequency == "monthly":
            day_of_month = (
                str(schedule.day_of_month)
                if schedule.day_of_month is not None
                else "*"
            )
            return f"{minute} {hour} {day_of_month} * *"
        msg = f"Unknown frequency: {schedule.frequency}"
        raise ValueError(msg)

    def generate_cron_command(self, schedule: Schedule) -> str:
        """Generate the dbcalm backup command that will be executed by cron."""
        # Build command to call dbcalm backup CLI
        return (
            f"/usr/bin/dbcalm backup {schedule.backup_type} "
            f">> /var/log/{self.config.PROJECT_NAME}/cron-{schedule.id}.log 2>&1"
        )

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

            lines.append(f"# Schedule ID: {schedule.id}")
            lines.append(f"{cron_expression} root {cron_command}")
            lines.append("")

        return "\n".join(lines)
