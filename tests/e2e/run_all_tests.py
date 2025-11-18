#!/usr/bin/env python3
"""Run all E2E test combinations in parallel threads.

This script:
1. Builds DEB and RPM packages in parallel
2. Runs E2E tests for all distribution and database combinations in parallel:
   - Debian + MariaDB
   - Debian + MySQL
   - Rocky + MariaDB
   - Rocky + MySQL

All tests run in parallel threads and continue even if one fails.
Output is written to both console and a shared log file.
"""
import argparse
import subprocess
import sys
import threading
from datetime import UTC, datetime
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""

    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


class TestRunner:
    """Manages parallel execution of builds and E2E test combinations."""

    def __init__(self, log_file: Path) -> None:
        """Initialize test runner.

        Args:
            log_file: Path to shared log file for all test output
        """
        self.log_file = log_file
        self.log_lock = threading.Lock()
        self.results = {}
        self.results_lock = threading.Lock()

        # Define build targets: (name, make_target, color)
        self.builds = {
            "DEB-BUILD": ("deb-docker", Colors.BLUE),
            "RPM-BUILD": ("rpm-docker", Colors.CYAN),
        }

        # Define test combinations: (name, make_target, color, docker_project_name)
        # Using -quick targets since packages are already built
        self.combinations = {
            "DEB-MARIADB": (
                "e2e-test-mariadb-deb-quick",
                Colors.BLUE,
                "dbcalm-e2e-deb-mariadb",
            ),
            "DEB-MYSQL": (
                "e2e-test-mysql-deb-quick",
                Colors.GREEN,
                "dbcalm-e2e-deb-mysql",
            ),
            "ROCKY-MARIADB": (
                "e2e-test-mariadb-rpm-quick",
                Colors.CYAN,
                "dbcalm-e2e-rpm-mariadb",
            ),
            "ROCKY-MYSQL": (
                "e2e-test-mysql-rpm-quick",
                Colors.MAGENTA,
                "dbcalm-e2e-rpm-mysql",
            ),
        }

    def log(self, prefix: str, message: str, color: str = "") -> None:
        """Thread-safe logging to both console and file.

        Args:
            prefix: Test combination prefix (e.g., "DEB-MARIADB")
            message: Message to log
            color: ANSI color code for console output
        """
        # Format message with prefix
        formatted = f"[{prefix}] {message}"

        # Write to console with color
        with self.log_lock:
            if color:
                print(f"{color}{formatted}{Colors.RESET}", flush=True)
            else:
                print(formatted, flush=True)

            # Write to log file (without color codes)
            with self.log_file.open("a") as f:
                timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{timestamp} {formatted}\n")

    def cleanup_docker_compose(self, project_name: str) -> None:
        """Clean up Docker Compose containers and volumes.

        Args:
            project_name: Docker Compose project name (e.g., "dbcalm-e2e-deb-mariadb")
        """
        try:
            # Run docker compose down -v to remove containers and volumes
            subprocess.run(
                ["docker", "compose", "-p", project_name, "down", "-v"],
                check=False,
                cwd=Path(__file__).parent / "common",
                capture_output=True,
                timeout=30,
            )
        except Exception as e:
            # Log cleanup failures but don't fail the test
            self.log("CLEANUP", f"Failed to cleanup {project_name}: {e}", Colors.YELLOW)

    def print_failed_test_logs(self) -> None:
        """Extract and print logs from containers of failed tests."""
        # Get list of failed test combinations
        failed_tests = [
            name for name, result in self.results.items()
            if name in self.combinations and not result["success"]
        ]

        if not failed_tests:
            return

        print()
        print("=" * 80)
        print(f"{Colors.BOLD}Container Logs for Failed Tests{Colors.RESET}")
        print("=" * 80)

        for test_name in failed_tests:
            # Get docker project name for this test
            _, _, project_name = self.combinations[test_name]

            print()
            print(
                f"{Colors.RED}{Colors.BOLD}=== Logs for {test_name} ==="
                f"{Colors.RESET}",
            )
            print()

            try:
                # Extract container logs using docker compose logs
                result = subprocess.run(
                    ["docker", "compose", "-p", project_name, "logs", "--no-color"],
                    check=False,
                    cwd=Path(__file__).parent / "common",
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0 and result.stdout:
                    # Print the logs
                    print(result.stdout)
                else:
                    print(
                        f"{Colors.YELLOW}No logs available for {test_name}"
                        f"{Colors.RESET}",
                    )

            except Exception as e:
                print(
                    f"{Colors.YELLOW}Failed to extract logs for "
                    f"{test_name}: {e}{Colors.RESET}",
                )

        print("=" * 80)

    def run_make_target(
        self, name: str, make_target: str, color: str, project_name: str | None = None,
    ) -> None:
        """Run a single make target in a thread.

        Args:
            name: Target name (e.g., "DEB-BUILD", "DEB-MARIADB")
            make_target: Make target to run (e.g., "deb-docker")
            color: ANSI color code for this target's output
            project_name: Docker Compose project name for cleanup
                (None for build targets)
        """
        self.log(name, f"Starting (make {make_target})", color)
        start_time = datetime.now(UTC)

        try:
            # Run make target and capture output
            process = subprocess.Popen(
                ["make", make_target],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # Line buffered
            )

            # Stream output line by line
            for line in process.stdout:  # type: ignore[union-attr]
                stripped_line = line.rstrip()
                if stripped_line:
                    self.log(name, stripped_line, color)

            # Wait for process to complete
            return_code = process.wait()

            # Calculate duration
            duration = datetime.now(UTC) - start_time
            duration_str = str(duration).split(".")[0]  # Remove microseconds

            # Log result
            if return_code == 0:
                self.log(
                    name,
                    f"✓ PASSED (duration: {duration_str})",
                    Colors.GREEN + Colors.BOLD,
                )
                success = True
            else:
                self.log(
                    name,
                    f"✗ FAILED with exit code {return_code} (duration: {duration_str})",
                    Colors.RED + Colors.BOLD,
                )
                success = False

        except Exception as e:
            duration = datetime.now(UTC) - start_time
            duration_str = str(duration).split(".")[0]
            self.log(
                name,
                f"✗ ERROR: {e} (duration: {duration_str})",
                Colors.RED + Colors.BOLD,
            )
            success = False
            return_code = -1

        # Clean up docker compose containers if this was a test
        if project_name:
            self.log(
                name,
                f"Cleaning up Docker containers (project: {project_name})",
                color,
            )
            self.cleanup_docker_compose(project_name)

        # Store result
        with self.results_lock:
            self.results[name] = {
                "success": success,
                "return_code": return_code,
                "duration": duration_str,
            }

    def run_builds(self) -> bool:
        """Run package builds in parallel.

        Returns:
            True if all builds passed, False otherwise
        """
        print()
        print("=" * 80)
        print(f"{Colors.BOLD}Phase 1: Building Packages{Colors.RESET}")
        print("=" * 80)
        print()

        # Create and start build threads
        threads = []
        for name, (make_target, color) in self.builds.items():
            thread = threading.Thread(
                target=self.run_make_target,
                args=(name, make_target, color),
                name=name,
            )
            thread.start()
            threads.append(thread)

        # Wait for all build threads to complete
        for thread in threads:
            thread.join()

        # Check if all builds passed
        all_passed = True
        for name in self.builds:
            if name in self.results and not self.results[name]["success"]:
                all_passed = False
                break

        if all_passed:
            print()
            print(
                f"{Colors.GREEN}{Colors.BOLD}✓ All builds completed "
                f"successfully{Colors.RESET}",
            )
        else:
            print()
            print(f"{Colors.RED}{Colors.BOLD}✗ Some builds failed{Colors.RESET}")

        return all_passed

    def run_tests(self, selected_tests: list[str] | None = None) -> bool:
        """Run test combinations in parallel.

        Args:
            selected_tests: List of test names to run, or None for all tests

        Returns:
            True if all tests passed, False otherwise
        """
        print()
        print("=" * 80)
        print(f"{Colors.BOLD}Phase 2: Running Tests{Colors.RESET}")
        print("=" * 80)
        print()

        # Filter combinations if specific tests selected
        if selected_tests:
            combinations = {
                k: v for k, v in self.combinations.items() if k in selected_tests
            }
        else:
            combinations = self.combinations

        # Create and start test threads
        threads = []
        for name, (make_target, color, project_name) in combinations.items():
            thread = threading.Thread(
                target=self.run_make_target,
                args=(name, make_target, color, project_name),
                name=name,
            )
            thread.start()
            threads.append(thread)

        # Wait for all test threads to complete
        for thread in threads:
            thread.join()

        # Check if all tests passed
        all_passed = True
        for name in combinations:
            if name in self.results and not self.results[name]["success"]:
                all_passed = False
                break

        return all_passed

    def run_all(  # noqa: PLR0915
        self,
        selected_tests: list[str] | None = None,
    ) -> bool:
        """Run builds and tests in sequence.

        Args:
            selected_tests: List of test names to run, or None for all tests

        Returns:
            True if all builds and tests passed, False otherwise
        """
        # Create log file header
        with self.log_file.open("w") as f:
            f.write("=" * 80 + "\n")
            f.write("E2E Test Run - Build and Test All Combinations\n")
            timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"Started: {timestamp}\n")
            f.write("=" * 80 + "\n\n")

        print(f"{Colors.BOLD}Starting E2E build and test process...{Colors.RESET}")
        print(f"Log file: {self.log_file}")

        # Phase 1: Build packages in parallel
        builds_passed = self.run_builds()

        # Only run tests if builds succeeded
        if not builds_passed:
            print()
            print(
                f"{Colors.RED}{Colors.BOLD}Builds failed. Skipping tests."
                f"{Colors.RESET}",
            )
            return False

        # Phase 2: Run tests in parallel
        tests_passed = self.run_tests(selected_tests)

        # Print container logs for failed tests
        self.print_failed_test_logs()

        # Print final summary
        print()
        print("=" * 80)
        print(f"{Colors.BOLD}Final Summary{Colors.RESET}")
        print("=" * 80)

        # Group results by phase
        build_results = {k: v for k, v in self.results.items() if k in self.builds}
        test_results = {k: v for k, v in self.results.items() if k in self.combinations}

        # Print build results
        print(f"\n{Colors.BOLD}Builds:{Colors.RESET}")
        for name in sorted(build_results.keys()):
            result = build_results[name]
            status_color = Colors.GREEN if result["success"] else Colors.RED
            status_symbol = "✓" if result["success"] else "✗"
            status_text = "PASSED" if result["success"] else "FAILED"

            print(
                f"  {status_color}{status_symbol} {name:15} {status_text:8} "
                f"(duration: {result['duration']}){Colors.RESET}",
            )

        # Print test results
        print(f"\n{Colors.BOLD}Tests:{Colors.RESET}")
        for name in sorted(test_results.keys()):
            result = test_results[name]
            status_color = Colors.GREEN if result["success"] else Colors.RED
            status_symbol = "✓" if result["success"] else "✗"
            status_text = "PASSED" if result["success"] else "FAILED"

            print(
                f"  {status_color}{status_symbol} {name:15} {status_text:8} "
                f"(duration: {result['duration']}){Colors.RESET}",
            )

        print("=" * 80)

        # Write summary to log file
        with self.log_file.open("a") as f:
            f.write("\n" + "=" * 80 + "\n")
            f.write("Final Summary\n")
            f.write("=" * 80 + "\n")
            f.write("\nBuilds:\n")
            for name in sorted(build_results.keys()):
                result = build_results[name]
                status = "PASSED" if result["success"] else "FAILED"
                f.write(
                    f"  {status} - {name} (duration: {result['duration']}, "
                    f"exit code: {result['return_code']})\n",
                )
            f.write("\nTests:\n")
            for name in sorted(test_results.keys()):
                result = test_results[name]
                status = "PASSED" if result["success"] else "FAILED"
                f.write(
                    f"  {status} - {name} (duration: {result['duration']}, "
                    f"exit code: {result['return_code']})\n",
                )
            f.write("=" * 80 + "\n")
            timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"Completed: {timestamp}\n")

        all_passed = builds_passed and tests_passed
        if all_passed:
            print(
                f"\n{Colors.GREEN}{Colors.BOLD}All builds and tests passed!"
                f"{Colors.RESET}",
            )
        else:
            print(
                f"\n{Colors.RED}{Colors.BOLD}Some builds or tests failed. "
                f"Check log file for details.{Colors.RESET}",
            )

        return all_passed


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build packages and run E2E tests for all combinations",
    )
    parser.add_argument(
        "--debian-mariadb",
        action="store_true",
        help="Run only Debian + MariaDB tests",
    )
    parser.add_argument(
        "--debian-mysql",
        action="store_true",
        help="Run only Debian + MySQL tests",
    )
    parser.add_argument(
        "--rocky-mariadb",
        action="store_true",
        help="Run only Rocky + MariaDB tests",
    )
    parser.add_argument(
        "--rocky-mysql",
        action="store_true",
        help="Run only Rocky + MySQL tests",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path(__file__).parent / "logs",
        help="Directory for log files (default: tests/e2e/logs)",
    )

    args = parser.parse_args()

    # Determine which tests to run
    selected_tests = []
    if args.debian_mariadb:
        selected_tests.append("DEB-MARIADB")
    if args.debian_mysql:
        selected_tests.append("DEB-MYSQL")
    if args.rocky_mariadb:
        selected_tests.append("ROCKY-MARIADB")
    if args.rocky_mysql:
        selected_tests.append("ROCKY-MYSQL")

    # If no specific tests selected, run all
    if not selected_tests:
        selected_tests = None

    # Create log directory
    args.log_dir.mkdir(parents=True, exist_ok=True)

    # Create log file with timestamp
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    log_file = args.log_dir / f"all-tests-{timestamp}.log"

    # Run builds and tests
    runner = TestRunner(log_file)
    all_passed = runner.run_all(selected_tests)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
