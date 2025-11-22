import argparse
import getpass
import sys

from dbcalm.data.model.user import User
from dbcalm.data.repository.user import UserRepository


def create_user(username: str, password: str) -> None:
    """Create a new user with hashed password"""
    user_repo = UserRepository()

    # Check if user already exists
    existing_user = user_repo.get(username)
    if existing_user:
        print(f"Error: User '{username}' already exists")
        sys.exit(1)

    user = User(username=username, password=password)
    created_user = user_repo.create(user)
    print(f"User '{created_user.username}' created successfully")


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
    except Exception as e:
        print(f"Error updating password: {e!s}")


def get_all_users() -> list[User]:
    """Get a list of all users"""
    user_repo = UserRepository()
    # get_list returns a tuple (list of users, total count)
    users, _ = user_repo.get_list(query=None, order=None, page=None, per_page=None)
    return users


def handle_add_command(args: argparse.Namespace) -> None:
    """Handle the add user command."""
    password = args.password
    if not password:
        password = getpass.getpass("Enter password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords do not match!")
            sys.exit(1)
    create_user(args.username, password)


def handle_delete_command(args: argparse.Namespace) -> None:
    """Handle the delete user command."""
    confirm = input(
        f"Are you sure you want to delete user '{args.username}'? (y/n): ",
    )
    if confirm.lower() == "y":
        delete_user(args.username)


def handle_update_password_command(args: argparse.Namespace) -> None:
    """Handle the update password command."""
    password = args.password
    if not password:
        password = getpass.getpass("Enter new password: ")
        confirm = getpass.getpass("Confirm new password: ")
        if password != confirm:
            print("Passwords do not match!")
            sys.exit(1)
    update_password(args.username, password)


def handle_list_command() -> None:
    """Handle the list users command."""
    users = get_all_users()
    if not users:
        print("No users found!")
        sys.exit(0)

    print("\nUsers:")
    for user in users:
        print(f"- {user.username}")


def run(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    """Handle user management commands"""
    # If no subcommand provided, show help
    if not hasattr(args, "users_command") or not args.users_command:
        parser.print_help()
        sys.exit(0)

    # Handle commands
    if args.users_command == "add":
        handle_add_command(args)
    elif args.users_command == "delete":
        handle_delete_command(args)
    elif args.users_command == "update-password":
        handle_update_password_command(args)
    elif args.users_command == "list":
        handle_list_command()


def configure_parser(
    subparsers: argparse._SubParsersAction,
) -> argparse.ArgumentParser:
    """Configure the users subcommand parser"""
    users_parser = subparsers.add_parser("users", help="Manage users")
    users_subparsers = users_parser.add_subparsers(
        dest="users_command",
        help="User command",
    )

    # Add user command
    add_parser = users_subparsers.add_parser("add", help="Add a new user")
    add_parser.add_argument("username", help="Username for the new user")
    add_parser.add_argument(
        "--password",
        help="Password for the new user (if not provided, will prompt)",
    )

    # Delete user command
    delete_parser = users_subparsers.add_parser(
        "delete",
        help="Delete an existing user",
    )
    delete_parser.add_argument("username", help="Username to delete")

    # Update password command
    update_parser = users_subparsers.add_parser(
        "update-password",
        help="Update password for an existing user",
    )
    update_parser.add_argument(
        "username",
        help="Username to update password for",
    )
    update_parser.add_argument(
        "--password",
        help="New password (if not provided, will prompt)",
    )

    # List users command
    users_subparsers.add_parser("list", help="List all users")

    return users_parser
