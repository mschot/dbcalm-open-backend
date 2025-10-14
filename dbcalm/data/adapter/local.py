from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlmodel import Session, SQLModel, create_engine

from dbcalm.config.config import Config
from dbcalm.data.adapter.adapter import Adapter
from dbcalm.logger.logger_factory import logger_factory


class Local(Adapter):
    def __init__(self) -> None:
        self.session  = self.session()
        self.logger = logger_factory()
        super().__init__()

    def session(self) -> Session:
        engine = create_engine(
            "sqlite:///" + Config.DB_PATH,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False,
            connect_args={"check_same_thread": False},

        )
        SQLModel.metadata.create_all(engine)

       # Create the database tables if they don't exist
        session_factory = sessionmaker(bind=engine, expire_on_commit=False)

        session = scoped_session(session_factory)

        return session()

    def get(self, model: SQLModel, query: dict) -> SQLModel|None:
        # Convert dict to list of QueryFilter objects (all equality)
        from dbcalm.util.parse_query_with_operators import QueryFilter  # noqa: PLC0415

        query_filters = []
        for key, value in query.items():
            query_filters.append(QueryFilter(field=key, operator="eq", value=value))

        result = self.get_list(model, query_filters)
        if len(result[0]) == 0:
            return None
        return result[0][0]

    def create(self, model: SQLModel) -> SQLModel:
        self.session.add(model)
        try:
            self.session.commit()
        except Exception:
            self.logger.exception("error committing")
            self.session.rollback()
            raise
        return model

    def update(self, model: SQLModel) -> SQLModel:
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return model

    def _apply_filter_operator(self, column, operator: str, value):  # noqa: ANN001, ANN202, PLR0911
        """Apply a filter operator to a column with a value."""
        if operator == "eq":
            return column == value
        if operator == "ne":
            return column != value
        if operator == "gt":
            return column > value
        if operator == "gte":
            return column >= value
        if operator == "lt":
            return column < value
        if operator == "lte":
            return column <= value
        if operator == "in":
            # For IN operator, convert each value in the list
            converted_values = [self._convert_value_type(column, v) for v in value]
            return column.in_(converted_values)
        if operator == "nin":
            # For NOT IN operator, convert each value in the list
            converted_values = [self._convert_value_type(column, v) for v in value]
            return ~column.in_(converted_values)
        return None

    def get_list(
        self,
        model: SQLModel,
        query: list | None = None,
        order: list | None = None,
        page: int | None = 1,
        per_page: int | None = 100,
    ) -> tuple[list[SQLModel], int]:
        select = self.session.query(model)

        # Apply filters with operators
        if query:
            for filter_obj in query:
                column = getattr(model, filter_obj.field)

                # Convert value to appropriate type based on column type
                value = self._convert_value_type(column, filter_obj.value)

                # Apply the filter operation
                filter_condition = self._apply_filter_operator(
                    column,
                    filter_obj.operator,
                    value,
                )
                if filter_condition is not None:
                    select = select.filter(filter_condition)

        count = select.count()

        # Apply ordering (uses .value from QueryFilter which contains direction)
        if order:
            for order_obj in order:
                column = getattr(model, order_obj.field)
                direction = order_obj.value.lower()
                select = select.order_by(
                    column.asc() if direction == "asc" else column.desc(),
                )

        # Apply pagination if page and per_page are provided, otherwise return all
        if page is not None and per_page is not None:
            items = select.offset((page - 1) * per_page).limit(per_page).all()
        else:
            items = select.all()

        return items, count

    def _convert_value_type(self, column, value: str):  # noqa: ANN202, ANN001, PLR0911
        """Convert string value to appropriate type based on column type."""
        # Try to get the column's Python type
        try:
            column_type = column.type.python_type
        except NotImplementedError:
            # Some types (like JSON) don't implement python_type
            # Return value as-is and let SQLAlchemy handle it
            return value

        # Handle datetime conversion
        if column_type is datetime:
            try:
                # Try ISO format first (e.g., "2025-10-01T00:00:00")
                return datetime.fromisoformat(value)
            except (ValueError, AttributeError):
                # If that fails, return as string and let SQLAlchemy handle it
                return value

        # Handle integer conversion
        if column_type is int:
            try:
                return int(value)
            except (ValueError, TypeError):
                return value

        # Handle float conversion
        if column_type is float:
            try:
                return float(value)
            except (ValueError, TypeError):
                return value

        # Handle boolean conversion
        if column_type is bool:
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes")
            return bool(value)

        # Return as string for all other types
        return value

    def delete(self, model: SQLModel, query: dict) -> bool:
        model = self.get(model, query)
        if model is None:
            return False

        self.session.delete(model)
        self.session.commit()
        return True

