from datetime import datetime, timezone

from backrest.logger.logger_factory import logger_factory
from backrest_client.client import Client

logger = logger_factory()

response = Client().command(
    "incremental_backup", {
        "identifier": datetime.now(tz=timezone.utc).strftime("%Y-%m-%d-%H-%M-%S"),
        "from_identifier": "2025-02-11-13-27-43",
    },
)

logger.debug(response)

