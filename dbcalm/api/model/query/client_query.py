from enum import Enum


class ClientQueryField(str, Enum):
    """Valid fields for querying clients."""

    ID = "id"
    LABEL = "label"
    SCOPES = "scopes"


class ClientOrderField(str, Enum):
    """Valid fields for ordering clients."""

    ID = "id"
    LABEL = "label"
