from backrest_client.client import Client
from datetime import datetime

response = Client().command(
    'incremental_backup', {'identifier': 'test123', 'from_identifier': '2025-02-11-13-27-43' }
)
print(response)