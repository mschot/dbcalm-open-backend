import argparse
import sys

from dbcalm.data.model.client import Client
from dbcalm.data.repository.client import ClientRepository


def create_client(label: str) -> None:
    """Create a new client with auto-generated credentials"""
    client_repo = ClientRepository()
    created_client = client_repo.create(label)
    print(f"Client '{created_client.label}' created successfully")
    print(f"Client ID: {created_client.id}")
    print(f"Client Secret: {created_client.secret}")
    print("\nIMPORTANT: Save the secret now - it will not be shown again!")


def delete_client(client_id: str) -> None:
    """Delete an existing client"""
    client_repo = ClientRepository()
    try:
        client = client_repo.get(client_id)
        if not client:
            print(f"Client '{client_id}' not found")
            return
        client_repo.delete(client_id)
        print(f"Client '{client.label}' (ID: {client_id}) deleted successfully")
    except Exception as e:
        print(f"Error deleting client: {e!s}")


def update_label(client_id: str, label: str) -> None:
    """Update label for an existing client"""
    client_repo = ClientRepository()
    try:
        client = client_repo.update_label(client_id, label)
        if not client:
            print(f"Client '{client_id}' not found")
            return
        print(f"Label updated successfully for client '{client_id}'")
    except Exception as e:
        print(f"Error updating label: {e!s}")


def get_all_clients() -> list[Client]:
    """Get a list of all clients"""
    client_repo = ClientRepository()
    clients, _ = client_repo.get_list(None, None, None, None)
    return clients


def run(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    """Handle client management commands"""
    # If no subcommand provided, show help
    if not hasattr(args, "clients_command") or not args.clients_command:
        parser.print_help()
        sys.exit(0)

    # Handle commands
    if args.clients_command == "add":
        create_client(args.label)

    elif args.clients_command == "delete":
        confirm = input(
            f"Are you sure you want to delete client '{args.client_id}'? (y/n): ",
        )
        if confirm.lower() == "y":
            delete_client(args.client_id)

    elif args.clients_command == "update":
        update_label(args.client_id, args.label)

    elif args.clients_command == "list":
        clients = get_all_clients()
        if not clients:
            print("No clients found!")
            sys.exit(0)

        print("\nClients:")
        for client in clients:
            print(f"- {client.label} (ID: {client.id})")


def configure_parser(
    subparsers: argparse._SubParsersAction,
) -> argparse.ArgumentParser:
    """Configure the clients subcommand parser"""
    clients_parser = subparsers.add_parser("clients", help="Manage API clients")
    clients_subparsers = clients_parser.add_subparsers(
        dest="clients_command",
        help="Client command",
    )

    # Add client command
    add_parser = clients_subparsers.add_parser("add", help="Add a new client")
    add_parser.add_argument("label", help="Label for the new client")

    # Delete client command
    delete_parser = clients_subparsers.add_parser(
        "delete",
        help="Delete an existing client",
    )
    delete_parser.add_argument("client_id", help="Client ID to delete")

    # Update client command
    update_parser = clients_subparsers.add_parser(
        "update",
        help="Update label for an existing client",
    )
    update_parser.add_argument("client_id", help="Client ID to update")
    update_parser.add_argument("label", help="New label for the client")

    # List clients command
    clients_subparsers.add_parser("list", help="List all clients")

    return clients_parser
