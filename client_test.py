from backrest_client.client import Client
from datetime import datetime

Client().command(
    'full_backup', {'identifier': datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}
)