from typing import Annotated

from fastapi import Query
from pydantic import AfterValidator

from app.schemas.common import ensure_storable_text

# Bounding the page keeps the SQL OFFSET far below PostgreSQL's bigint limit.
MAX_PAGE = 100_000


def optional_storable_text(value: str | None) -> str | None:
    return value if value is None else ensure_storable_text(value)


PageQuery = Annotated[int, Query(ge=1, le=MAX_PAGE)]
PageSizeQuery = Annotated[int, Query(ge=1, le=100)]
SearchQuery = Annotated[str | None, Query(max_length=100), AfterValidator(optional_storable_text)]
