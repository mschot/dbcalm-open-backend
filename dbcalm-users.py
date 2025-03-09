#!/usr/bin/env python3

import argparse
import getpass
import sys

from dbcalm.data.model.user import User
from dbcalm.data.repository.user import UserRepository


def create_user(username: str, password: str) -> None:
    """Create a new user with hashed password"""
    user = User(username=username, password=password)
    user_repo = UserRepository()
    created_user = user_repo.create(user)
    print(f"User '{created_user.username}' created successfully")
    print("Password has been hashed")


def delete_user(username: str) -> None:
    """Delete an existing user"""
    user_repo = UserRepository()
    try:
        user = user_repo.get(username)
        if not user:
            print(f"User '{username}' not found")
            return
        user_repo.delete(username)
        print(f"User '{username}' deleted successfully")
    except Exception as e:
        print(f"Error deleting user: {e!s}")


def update_password(username: str, password: str) -> None:
    """Update password for an existing user"""
    user_repo = UserRepository()
    try:
        user = user_repo.get(username)
        if not user:
            print(f"User '{username}' not found")
            return
        user.password = password
        user_repo.update(user)
        print(f"Password updated successfully for user '{username}'")
        print("Password has been hashed")
    except Exception as e:
        print(f"Error updating password: {e!s}")


def get_all_users() -> list[User]:
    """Get a list of all users"""
    user_repo = UserRepository()
    # get_list returns a tuple (list of users, total count)
    users, _ = user_repo.adapter.get_list(User, {})
    return users


def display_user_selection(users: list[User]) -> str:
    """Display a list of users for selection and return the selected username"""
    if not users:
        print("No users found!")
        return ""

    print("\nAvailable users:")
    for i, user in enumerate(users, 1):
        print(f"{i}. {user.username}")

    print("0. Back")

    while True:
        try:
            selection = input("\nSelect user (number) or type username: ")

            # Check if input is back option
            if selection == "0":
                return ""

            # Check if input is a number and within range
            if selection.isdigit() and 1 <= int(selection) <= len(users):
                return users[int(selection) - 1].username

            # Check if input matches an existing username
            for user in users:
                if selection == user.username:
                    return selection

            print("Invalid selection. Please try again.")
        except (ValueError, IndexError):
            print("Invalid selection. Please try again.")


def interactive_mode() -> None:  # noqa: C901
    """Run the CLI in interactive mode with menu options"""
    while True:
        print("\nDBCalm User Management")
        print("======================")
        print("1. Add user")
        print("2. Delete user")
        print("3. Update user password")
        print("0. Exit")

        choice = input("\nSelect an option: ")

        if choice == "1":
            username = input("Enter username: ")
            password = getpass.getpass("Enter password: ")
            confirm = getpass.getpass("Confirm password: ")

            if password != confirm:
                print("Passwords do not match!")
                continue

            create_user(username, password)

        elif choice == "2":
            users = get_all_users()
            username = display_user_selection(users)

            if not username:
                continue

            confirm = input(
                f"Are you sure you want to delete user '{username}'? (y/n): "
            )

            if confirm.lower() == "y":
                delete_user(username)

        elif choice == "3":
            users = get_all_users()
            username = display_user_selection(users)

            if not username:
                continue

            password = getpass.getpass("Enter new password: ")
            confirm = getpass.getpass("Confirm new password: ")

            if password != confirm:
                print("Passwords do not match!")
                continue

            update_password(username, password)

        elif choice == "0":
            print("Exiting...")
            break

        else:
            print("Invalid option. Please try again.")


def main() -> None:  # noqa: C901, PLR0912, PLR0915
    """Main function to handle CLI arguments"""
    parser = argparse.ArgumentParser(description="DBCalm User Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Add user command
    add_parser = subparsers.add_parser("add", help="Add a new user")
    add_parser.add_argument("username", help="Username for the new user")
    add_parser.add_argument(
        "--admin",
        "--password", help="Password for the new user (if not provided, will prompt)"
    )

    # Delete user command
    delete_parser = subparsers.add_parser("delete", help="Delete an existing user")
    delete_parser.add_argument(
        "username",
        nargs="?",
        help="Username to delete (if not provided, will show a list)",
    )

    # Update password command
    update_parser = subparsers.add_parser(
        "update-password",
        help="Update password for an existing user",
    )
    update_parser.add_argument(
        "username",
        nargs="?",
        help="Username to update password for (if not provided, will show a list)",
    )
    update_parser.add_argument(
        "--password",
        help="New password (if not provided, will prompt)",
    )

    # List users command
    subparsers.add_parser("list", help="List all users")

    args = parser.parse_args()

    # If no command provided, run interactive mode
    if not args.command:
        interactive_mode()
        return

    # Handle commands
    if args.command == "add":
        password = args.password
        if not password:
            password = getpass.getpass("Enter password: ")
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                print("Passwords do not match!")
                sys.exit(1)
        create_user(args.username, password)

    elif args.command == "delete":
        if not args.username:
            users = get_all_users()
            username = display_user_selection(users)
            if not username:
                print("Operation cancelled.")
                sys.exit(0)
        else:
            username = args.username

        confirm = input(f"Are you sure you want to delete user '{username}'? (y/n): ")
        if confirm.lower() == "y":
            delete_user(username)

    elif args.command == "update-password":
        if not args.username:
            users = get_all_users()
            username = display_user_selection(users)
            if not username:
                print("Operation cancelled.")
                sys.exit(0)
        else:
            username = args.username

        password = args.password
        if not password:
            password = getpass.getpass("Enter new password: ")
            confirm = getpass.getpass("Confirm new password: ")
            if password != confirm:
                print("Passwords do not match!")
                sys.exit(1)
        update_password(username, password)

    elif args.command == "list":
        users = get_all_users()
        if not users:
            print("No users found!")
            sys.exit(0)

        print("\nUsers:")
        for user in users:
            print(f"- {user.username}")


if __name__ == "__main__":
    main()
