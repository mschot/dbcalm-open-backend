from datetime import UTC, datetime

from dbcalm.logger.logger_factory import logger_factory
from dbcalm_cmd_client.client import Client

logger = logger_factory()

response = Client().command(
    "incremental_backup", {
        "identifier": datetime.now(tz=UTC).strftime("%Y-%m-%d-%H-%M-%S"),
        "from_identifier": "2025-02-11-13-27-43",
    },
)

logger.debug(response)

