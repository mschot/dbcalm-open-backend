import re
import subprocess
from pathlib import Path

from dbcalm.config.config_factory import config_factory
from dbcalm.data.model.schedule import Schedule


class CronManager:
    def __init__(self) -> None:
        self.config = config_factory()
        self.cron_dir = Path("/etc/cron.d")

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

    def sanitize_filename(self, text: str) -> str:
        """Sanitize text for use in filename (alphanumeric, dash, underscore only)."""
        return re.sub(r"[^a-zA-Z0-9_-]", "", text.replace(" ", "_"))

    def get_cron_filename(self, schedule_id: int) -> Path:
        """Get the cron file path for a schedule."""
        return self.cron_dir / f"{self.config.PROJECT_NAME}-schedule-{schedule_id}"

    def write_cron_file(self, schedule: Schedule) -> None:
        """Create or update a cron file for the schedule."""
        if schedule.id is None:
            msg = "Schedule must have an ID before creating cron file"
            raise ValueError(msg)

        cron_file = self.get_cron_filename(schedule.id)

        # Only write if enabled
        if not schedule.enabled:
            # If file exists and schedule is disabled, remove it
            if cron_file.exists():
                self.remove_cron_file(schedule.id)
            return

        cron_expression = self.generate_cron_expression(schedule)
        cron_command = self.generate_cron_command(schedule)

        # Create cron file content
        content = (
            f"# DBCalm Schedule: {schedule.title}\n"
            f"# Backup Type: {schedule.backup_type}\n"
            f"# Frequency: {schedule.frequency}\n"
            f"{cron_expression} root {cron_command}\n"
        )

        # Write to cron file
        cron_file.write_text(content)

        # Set correct permissions (644)
        cron_file.chmod(0o644)

    def remove_cron_file(self, schedule_id: int) -> None:
        """Remove the cron file for a schedule."""
        cron_file = self.get_cron_filename(schedule_id)

        if cron_file.exists():
            cron_file.unlink()

    def reload_cron(self) -> None:
        """Reload cron daemon to pick up changes (optional, cron.d is auto-reloaded)."""
        try:
            subprocess.run(  # noqa: S603
                ["systemctl", "reload", "cron"],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            # On systems without systemd or where cron service has a different name
            pass
