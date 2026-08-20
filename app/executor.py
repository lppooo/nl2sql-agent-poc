from __future__ import annotations

import time
from dataclasses import dataclass

from sqlalchemy import text

from app.database import get_engine
from app.models import QueryResult


@dataclass
class ExecutionError(Exception):
    message: str


def execute_sql(sql: str) -> QueryResult:
    start = time.perf_counter()
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        columns = list(result.keys())
        rows = [dict(row._mapping) for row in result.fetchall()]
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    return QueryResult(columns=columns, rows=rows, row_count=len(rows), elapsed_ms=elapsed_ms)
