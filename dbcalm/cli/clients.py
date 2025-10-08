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


def display_client_selection(clients: list[Client]) -> str:
    """Display a list of clients for selection and return the selected client ID"""
    if not clients:
        print("No clients found!")
        return ""

    print("\nAvailable clients:")
    for i, client in enumerate(clients, 1):
        print(f"{i}. {client.label} (ID: {client.id})")

    print("0. Back")

    while True:
        try:
            selection = input("\nSelect client (number) or type client ID: ")

            # Check if input is back option
            if selection == "0":
                return ""

            # Check if input is a number and within range
            if selection.isdigit() and 1 <= int(selection) <= len(clients):
                return clients[int(selection) - 1].id

            # Check if input matches an existing client ID
            for client in clients:
                if selection == client.id:
                    return selection

            print("Invalid selection. Please try again.")
        except (ValueError, IndexError):
            print("Invalid selection. Please try again.")


def interactive_mode() -> None:  # noqa: C901
    """Run the CLI in interactive mode with menu options"""
    while True:
        print("\nDBCalm Client Management")
        print("========================")
        print("1. Add client")
        print("2. Delete client")
        print("3. Update client label")
        print("4. List clients")
        print("0. Exit")

        choice = input("\nSelect an option: ")

        if choice == "1":
            label = input("Enter client label: ")
            create_client(label)

        elif choice == "2":
            clients = get_all_clients()
            client_id = display_client_selection(clients)

            if not client_id:
                continue

            confirm = input(
                f"Are you sure you want to delete client '{client_id}'? (y/n): "
            )

            if confirm.lower() == "y":
                delete_client(client_id)

        elif choice == "3":
            clients = get_all_clients()
            client_id = display_client_selection(clients)

            if not client_id:
                continue

            label = input("Enter new label: ")
            update_label(client_id, label)

        elif choice == "4":
            clients = get_all_clients()
            if not clients:
                print("No clients found!")
                continue

            print("\nClients:")
            for client in clients:
                print(f"- {client.label} (ID: {client.id})")

        elif choice == "0":
            print("Exiting...")
            break

        else:
            print("Invalid option. Please try again.")


def run(args: argparse.Namespace) -> None:  # noqa: C901, PLR0912
    """Handle client management commands"""
    # If no subcommand provided, run interactive mode
    if not hasattr(args, "clients_command") or not args.clients_command:
        interactive_mode()
        return

    # Handle commands
    if args.clients_command == "add":
        create_client(args.label)

    elif args.clients_command == "delete":
        if not args.client_id:
            clients = get_all_clients()
            client_id = display_client_selection(clients)
            if not client_id:
                print("Operation cancelled.")
                sys.exit(0)
        else:
            client_id = args.client_id

        confirm = input(f"Are you sure you want to delete client '{client_id}'? (y/n): ")
        if confirm.lower() == "y":
            delete_client(client_id)

    elif args.clients_command == "update":
        if not args.client_id:
            clients = get_all_clients()
            client_id = display_client_selection(clients)
            if not client_id:
                print("Operation cancelled.")
                sys.exit(0)
        else:
            client_id = args.client_id

        label = args.label
        if not label:
            label = input("Enter new label: ")
        update_label(client_id, label)

    elif args.clients_command == "list":
        clients = get_all_clients()
        if not clients:
            print("No clients found!")
            sys.exit(0)

        print("\nClients:")
        for client in clients:
            print(f"- {client.label} (ID: {client.id})")


def configure_parser(subparsers: argparse._SubParsersAction) -> None:
    """Configure the clients subcommand parser"""
    clients_parser = subparsers.add_parser("clients", help="Manage API clients")
    clients_subparsers = clients_parser.add_subparsers(dest="clients_command", help="Client command")

    # Add client command
    add_parser = clients_subparsers.add_parser("add", help="Add a new client")
    add_parser.add_argument("label", help="Label for the new client")

    # Delete client command
    delete_parser = clients_subparsers.add_parser("delete", help="Delete an existing client")
    delete_parser.add_argument(
        "client_id",
        nargs="?",
        help="Client ID to delete (if not provided, will show a list)",
    )

    # Update client command
    update_parser = clients_subparsers.add_parser(
        "update",
        help="Update label for an existing client",
    )
    update_parser.add_argument(
        "client_id",
        nargs="?",
        help="Client ID to update (if not provided, will show a list)",
    )
    update_parser.add_argument(
        "--label",
        help="New label (if not provided, will prompt)",
    )

    # List clients command
    clients_subparsers.add_parser("list", help="List all clients")
