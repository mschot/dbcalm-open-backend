import uuid
from queue import Queue

from dbcalm.data.model.process import Process
from dbcalm.data.model.schedule import Schedule
from dbcalm.logger.logger_factory import logger_factory
from dbcalm.service.cron_file_builder import CronFileBuilder
from dbcalm_cmd.adapter import adapter
from dbcalm_cmd.process.runner import Runner


class SystemCommands(adapter.Adapter):
    def __init__(
            self,
            command_runner: Runner,
        ) -> None:
        self.command_runner = command_runner
        self.logger = logger_factory()
        self.cron_file_builder = CronFileBuilder()

    def update_cron_schedules(self, schedules: list) -> tuple[Process, Queue]:
        """Update /etc/cron.d/dbcalm with all schedules.

        Writes complete cron file atomically by:
        1. Converting schedule dicts to Schedule models
        2. Building complete cron file content
        3. Writing to temp file
        4. Setting permissions
        5. Moving atomically to /etc/cron.d/dbcalm
        """
        # Convert list of dicts to Schedule objects
        schedule_objects = []
        for s_dict in schedules:
            schedule = Schedule(**s_dict)
            schedule_objects.append(schedule)

        # Build complete cron file content
        cron_content = self.cron_file_builder.build_cron_file_content(schedule_objects)

        # Create temp file path
        temp_file = f"/tmp/dbcalm-cron-{uuid.uuid4()}.tmp"
        target_file = "/etc/cron.d/dbcalm"

        # Write content to temp file, set permissions, then move atomically
        # Using shell to handle multi-step operation atomically
        command = [
            "/bin/sh",
            "-c",
            f'echo "{cron_content}" > {temp_file} && '
            f'chmod 644 {temp_file} && '
            f'mv {temp_file} {target_file}',
        ]

        return self.command_runner.execute(
            command=command,
            command_type="update_cron_schedules",
            args={"schedule_count": len(schedules)},
        )
