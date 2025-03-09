#!/usr/bin/env python3

import atexit
import hashlib
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path


def tail_log(log_file: str, stop_event: threading.Event) -> None:
    """Continuously reads and prints new log entries from the specified file."""
    try:
        # Use subprocess to tail the log file, only showing new lines (-n 0)
        tail_process = subprocess.Popen(  # noqa: S603
            ["tail", "-f", "-n", "0", log_file],  # noqa: S607
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            preexec_fn=os.setsid,  # noqa: PLW1509
        )

        # Read and print log lines until stop_event is set
        while not stop_event.is_set():
            line = tail_process.stdout.readline()
            if line:
                print(f"LOG: {line.rstrip()}")
            else:
                time.sleep(0.1)

        # Clean up the tail process
        os.killpg(os.getpgid(tail_process.pid), signal.SIGTERM)
    except FileNotFoundError:
        print(f"Warning: Log file {log_file} not found. Will try again...")
        time.sleep(2)  # Wait a bit before retrying
        if not stop_event.is_set():
            tail_log(log_file, stop_event)
    except Exception as e:
        print(f"Error tailing log file: {e}")


def kill_processes(processes: list[subprocess.Popen]) -> None:
    for process in processes:
        if process and process.poll() is None:  # Check if process is still running
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                print(f"Terminated process {process.pid}")
            except Exception as e:
                print(f"Error terminating process {process.pid}: {e}")


def scan_for_python_files(directory: str) -> dict[str, str]:
    """
    Scan the directory for Python files and return a dictionary with
    file paths as keys and their hash values as values.
    """
    file_hashes = {}
    for path in Path(directory).rglob("*.py"):
        try:
            if ".venv" not in str(path) and "__pycache__" not in str(path):
                file_hash = hashlib.md5(path.read_bytes()).hexdigest()  # noqa: S324
                file_hashes[str(path)] = file_hash
        except (PermissionError, FileNotFoundError):
            pass
    return file_hashes


def file_watcher(
        directory: str,
        restart_event: threading.Event,
        stop_event: threading.Event,
    ) -> None:
    """
    Watch for changes in Python files in the specified directory.
    If changes are detected, set the restart_event.
    """
    print(f"Watching for changes in {directory}")
    previous_hashes = scan_for_python_files(directory)

    while not stop_event.is_set():
        time.sleep(1)  # Check every second
        current_hashes = scan_for_python_files(directory)

        # Check if any files were added, removed, or modified
        if current_hashes != previous_hashes:
            changed_files = set(current_hashes.items()) ^ set(previous_hashes.items())
            for file_path, _ in changed_files:
                if file_path in current_hashes and file_path in previous_hashes:
                    print(f"File changed: {file_path}")
                elif file_path in current_hashes:
                    print(f"New file detected: {file_path}")
                else:
                    print(f"File removed: {file_path}")

            previous_hashes = current_hashes
            restart_event.set()


def start_processes() -> list[subprocess.Popen]:
    """Start the API and CMD server processes."""
    # Start API process
    api_process = subprocess.Popen(  # noqa: S603
        ["python", "dbcalm-api.py"],  # noqa: S607
        preexec_fn=os.setsid,  # noqa: PLW1509
    )
    print(f"Started API process with PID {api_process.pid}")

    # Start CMD server process
    cmd_server_process = subprocess.Popen(  # noqa: S603
        ["python", "dbcalm-cmd-server.py"],  # noqa: S607
        preexec_fn=os.setsid,  # noqa: PLW1509
    )
    print(f"Started CMD Server process with PID {cmd_server_process.pid}")

    return [api_process, cmd_server_process]


def signal_handler(sig, frame) -> None:  # noqa: ANN001, ARG001
    print("\nCaught signal, terminating child processes...")
    stop_event.set()  # Signal all monitoring threads to stop
    kill_processes(processes)
    sys.exit(0)


# Initialize events for thread synchronization
stop_event = threading.Event()
restart_event = threading.Event()

# Change cwd to parent directory
os.chdir("..")
parent_dir = os.getcwd()  # noqa: PTH109

# Start with empty process list
processes = []  # type: list[subprocess.Popen]

# Register cleanup handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
atexit.register(lambda: (stop_event.set(), kill_processes(processes)))

# Initial process start
try:
    print("Starting processes...")
    processes = start_processes()
except Exception as e:
    print(f"Failed to start processes: {e}")
    stop_event.set()
    sys.exit(1)

# Start file watcher in a separate thread
watcher_thread = threading.Thread(
    target=file_watcher,
    args=(parent_dir, restart_event, stop_event),
)
watcher_thread.daemon = True
watcher_thread.start()

# Start log tailing in a separate thread after processes have started
log_file = "/var/log/dbcalm/dbcalm.log"
log_thread = threading.Thread(target=tail_log, args=(log_file, stop_event))
log_thread.daemon = True
log_thread.start()
print(f"Tailing log file: {log_file} (showing only new entries)")

print("Press Ctrl+C to terminate all processes")

# Main loop - restarts processes when changes are detected
while True:
    try:
        # Wait for restart event or process termination
        while not restart_event.is_set() and all(p.poll() is None for p in processes):
            time.sleep(0.5)

        if restart_event.is_set():
            print("\n--- File changes detected, restarting processes ---")
            kill_processes(processes)
            time.sleep(1)  # Give processes time to terminate
            processes = start_processes()
            restart_event.clear()
        else:
            # If we got here without restart_event,
            # then a process terminated unexpectedly
            terminated = [i for i, p in enumerate(processes) if p.poll() is not None]
            for idx in terminated:
                print(
                    f"Process {processes[idx].pid} terminated"
                    f" unexpectedly with code {processes[idx].poll()}",
                )

            print("Restarting terminated processes...")
            kill_processes(processes)  # Make sure all processes are terminated
            time.sleep(1)
            processes = start_processes()

    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"Error in main loop: {e}")
        time.sleep(5)  # Wait a bit before retrying

# Ensure cleanup
stop_event.set()
kill_processes(processes)
