from enum import Enum

from fastapi import HTTPException
from pydantic import BaseModel


class QueryOperator(str, Enum):
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NIN = "nin"
    ISNULL = "isnull"
    ISNOTNULL = "isnotnull"


class QueryFilter(BaseModel):
    field: str
    operator: str
    value: str | list[str] | None = None


def parse_query_with_operators(query_str: str | None) -> list[QueryFilter]:
    """Parse query string into list of QueryFilter objects.

    Supports multiple formats:
    - 2 parts (field|value): Defaults to equality operator
    - 2 parts (field|isnull or field|isnotnull): Null check operators
    - 3 parts (field|operator|value): Uses specified operator

    Args:
        query_str: Query string in format "field|value" or "field|operator|value"
                  Multiple conditions separated by commas

    Returns:
        List of QueryFilter objects

    Examples:
        "status|completed" ->
            [QueryFilter(field='status', operator='eq', value='completed')]
        "start_time|gte|2025-10-02" ->
            [QueryFilter(field='start_time', operator='gte',
                        value='2025-10-02')]
        "status|in|running,completed" ->
            [QueryFilter(field='status', operator='in',
                        value=['running', 'completed'])]
        "from_backup_id|isnull" ->
            [QueryFilter(field='from_backup_id', operator='isnull', value=None)]
    """
    filters = []
    if not query_str:
        return filters

    valid_operators = {op.value for op in QueryOperator}

    for pair in query_str.split(","):
        parts = pair.split("|")

        if len(parts) == 2:  # noqa: PLR2004
            # 2 parts: could be field|value (default to eq) or field|isnull/isnotnull
            potential_operator = parts[1].lower()
            if potential_operator in ["isnull", "isnotnull"]:
                # field|isnull or field|isnotnull (no value needed)
                filters.append(
                    QueryFilter(
                        field=parts[0],
                        operator=potential_operator,
                        value=None,
                    ),
                )
            else:
                # field|value (default to eq)
                filters.append(
                    QueryFilter(
                        field=parts[0],
                        operator="eq",
                        value=parts[1],
                    ),
                )
        elif len(parts) == 3:  # noqa: PLR2004
            # 3 parts: field|operator|value
            operator = parts[1].lower()
            if operator not in valid_operators:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Invalid operator: {operator}. "
                        f"Valid operators: {', '.join(valid_operators)}"
                    ),
                )

            # Split value by comma for IN/NIN operators
            value = (
                parts[2].split(",") if operator in ["in", "nin"] else parts[2]
            )

            filters.append(
                QueryFilter(
                    field=parts[0],
                    operator=operator,
                    value=value,
                ),
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid query format: {pair}. "
                    "Expected 'field|value' or 'field|operator|value'"
                ),
            )

    return filters
