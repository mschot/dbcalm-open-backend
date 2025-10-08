#!/usr/bin/env python3

import argparse
import sys

from dbcalm.cli import backup, clients, server, users


def main() -> None:
    """Main entry point for dbcalm CLI"""
    parser = argparse.ArgumentParser(
        description="DBCalm - Database Backup and Management Tool",
        prog="dbcalm",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.0.1",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Server command
    subparsers.add_parser("server", help="Start the API server")

    # Users command
    users.configure_parser(subparsers)

    # Clients command
    clients.configure_parser(subparsers)

    # Backup command
    backup.configure_parser(subparsers)

    args = parser.parse_args()

    # If no command provided, show help
    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Route to appropriate handler
    if args.command == "server":
        server.run()
    elif args.command == "users":
        users.run(args)
    elif args.command == "clients":
        clients.run(args)
    elif args.command == "backup":
        backup.run(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
