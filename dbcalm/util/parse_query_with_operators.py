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


class QueryFilter(BaseModel):
    field: str
    operator: str
    value: str | list[str]


def parse_query_with_operators(query_str: str | None) -> list[QueryFilter]:
    """Parse query string into list of QueryFilter objects.

    Supports two formats:
    - 2 parts (field|value): Defaults to equality operator
    - 3 parts (field|operator|value): Uses specified operator

    Args:
        query_str: Query string in format "field|value" or "field|operator|value"
                  Multiple conditions separated by commas

    Returns:
        List of QueryFilter objects

    Examples:
        "status|completed" -> [QueryFilter(field='status', operator='eq', value='completed')]
        "start_time|gte|2025-10-02" -> [QueryFilter(field='start_time', operator='gte', value='2025-10-02')]
        "status|in|running,completed" -> [QueryFilter(field='status', operator='in', value=['running', 'completed'])]
    """
    filters = []
    if not query_str:
        return filters

    valid_operators = {op.value for op in QueryOperator}

    for pair in query_str.split(","):
        parts = pair.split("|")

        if len(parts) == 2:
            # 2 parts: field|value (default to eq)
            filters.append(QueryFilter(
                field=parts[0],
                operator="eq",
                value=parts[1],
            ))
        elif len(parts) == 3:
            # 3 parts: field|operator|value
            operator = parts[1].lower()
            if operator not in valid_operators:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid operator: {operator}. Valid operators: {', '.join(valid_operators)}",
                )

            # Split value by comma for IN/NIN operators
            value = parts[2].split(",") if operator in ["in", "nin"] else parts[2]

            filters.append(QueryFilter(
                field=parts[0],
                operator=operator,
                value=value,
            ))
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid query format: {pair}. Expected 'field|value' or 'field|operator|value'",
            )

    return filters
