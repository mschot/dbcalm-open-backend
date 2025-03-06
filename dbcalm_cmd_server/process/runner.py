import subprocess
import threading
import uuid
from datetime import UTC, datetime
from queue import Queue

from dbcalm.data.adapter.adapter_factory import (
    adapter_factory as data_adapter_factory,
)
from dbcalm.data.model.process import Process
from dbcalm.data.repository.process import ProcessRepository
from dbcalm.logger.logger_factory import logger_factory


class Runner:
    def __init__(self) -> None:
        self.data_adapter = data_adapter_factory()
        self.logger = logger_factory()

    def create_process(  # noqa: PLR0913
            self, pid: int,
            command: str,
            command_id: str,
            start_time: datetime,
            command_type: str,
            args: dict | None=None,
        ) -> Process:
        return self.data_adapter.create(
            Process(
                pid=pid,
                command=command,
                command_id=command_id,
                start_time=start_time,
                type=command_type,
                args=args,
                status="running",
            ),
        )

    def update_process(
            self,
            process: Process,
            end_time: datetime,
            stdout: str,
            stderr: str,
            returncode: int,
        ) -> Process:
        status = "success" if returncode == 0 else "failed"
        process.output = stdout
        process.error = stderr
        process.return_code = returncode
        process.end_time = end_time
        process.status = status
        self.data_adapter.update(process)
        return process

    def execute(
            self,
            command: list,
            command_type: str,
            command_id: str | None=None,
            args: dict | None=None,
            queue: Queue | None=None,
        ) -> tuple[Process, Queue]:
        if args is None:
            args = {}
        start_time = datetime.now(tz=UTC)
        process = subprocess.Popen(  # noqa: S603
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if command_id is None:
            command_id = self.generate_command_id()

        process_model = self.create_process(
            pid=process.pid,
            command=" ".join(command),
            command_id=command_id,
            start_time=start_time,
            command_type=command_type,
            args=args,
        )
        if queue is None:
            queue = Queue()

        def capture_output() -> None:
            end_time = datetime.now(tz=UTC)
            stdout, stderr = process.communicate()
            self.update_process(
                process_model,
                end_time,
                stdout,
                stderr,
                process.returncode,
            )
            queue.put(process_model)

        threading.Thread(target=capture_output, daemon=False).start()
        return process_model, queue

    def run_commands(  # noqa: PLR0913
            self,
            commands: list[list[str]],
            command_type: str,
            command_id: str,
            args: dict | None=None,
            master_queue: Queue | None=None,
            has_one_queue: Queue | None=None,
        ) -> None:
            local_queue = Queue()
            finished_processes = []
            try:
                self.logger.debug("Running commands consecutively: %s", commands)
                for index, command in enumerate(commands, 1):
                    self.logger.debug(
                        "Starting command %d of %d: %s",
                        index,
                        len(commands),
                        command,
                    )
                    process_model, _ = self.execute(
                        command,
                        command_type,
                        command_id,
                        args,
                        queue=local_queue,
                    )

                    if index == 1:
                        has_one_queue.put(process_model)

                    # Wait for the command to complete
                    completed_process = local_queue.get()
                    self.logger.debug(
                        "Command %s completed with return code: %s",
                        index,
                        completed_process.return_code,
                    )

                   # Add the completed process to the list
                   # of finished processes to be added to the master queue
                   # for further processing outside of the runner
                    finished_processes.append(completed_process)

                    if completed_process.return_code != 0:
                        self.logger.error(
                                "Command %d failed: %s with return code %d",
                                index,
                                completed_process.command,
                                completed_process.return_code,
                        )
                        break

                    if index == len(commands):
                        self.logger.debug(
                            "All %d commands completed successfully",
                            len(commands),
                        )
            except Exception:
                self.logger.exception("Error in run_commands")
            finally:
                for process in finished_processes:
                    master_queue.put(process)

    def execute_consecutive(
            self,
            commands: list[list],
            command_type: str,
            args: dict | None=None,
        ) -> tuple[list[Process], Queue]:
        command_id = self.generate_command_id()
        master_queue = Queue()
        has_one_queue = Queue()

        thread = threading.Thread(target=self.run_commands, args=(commands,
            command_type,
            command_id,
            args,
            master_queue,
            has_one_queue,
        ), daemon=False)
        thread.start()

        first_process = has_one_queue.get()

        return first_process, master_queue

    def generate_command_id(self) -> str:
        command_id = None
        while command_id is None:
            check_command_id = str(uuid.uuid4())
            #highly unlikely to have a duplicate id but just in case
            if ProcessRepository().by_command_id(check_command_id) is None:
                command_id = check_command_id
        return command_id
