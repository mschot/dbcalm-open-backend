import subprocess
import threading
from datetime import UTC, datetime
from queue import Queue

from backrest.data.adapter.adapter_factory import (
    adapter_factory as data_adapter_factory,
)
from backrest.data.model.process import Process


class Runner:
    def __init__(self) -> None:
        self.data_adapter = data_adapter_factory()

    def create_process(
            self, pid: int,
            command: str,
            start_time: datetime,
            command_type: str,
            args: dict | None=None,
        ) -> Process:
        return self.data_adapter.create(
            Process(
                pid=pid,
                command=command,
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
        return Process

    def execute(
            self,
            command: list,
            command_type: str,
            args: dict | None=None,
        ) -> Process:
        if args is None:
            args = {}
        start_time = datetime.now(tz=UTC)
        process = subprocess.Popen(  # noqa: S603
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        process_model = self.create_process(
            process.pid,
            " ".join(command),
            start_time,
            command_type,
            args,
        )
        queue = Queue()
        def capture_output() -> None:
            end_time = datetime.now(tz=UTC)
            stdout, stderr = process.communicate()
            #save changes to db
            self.update_process(
                process_model,
                end_time,
                stdout,
                stderr,
                process.returncode,
            )
            #put process in queue to be picked up when done
            queue.put(process_model)


        # Run the output capture in a separate thread
        threading.Thread(target=capture_output, daemon=True).start()
        return process_model, queue
