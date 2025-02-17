from backrest_client.client import Client

response = Client().command(
    "incremental_backup", {
        "identifier": "test12345",
        "from_identifier": "2025-02-11-13-27-43",
    },
)
print(response)
