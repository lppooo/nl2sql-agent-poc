from __future__ import annotations

import sqlglot
from sqlglot import exp

from app.config import get_settings
from app.models import ValidationResult


DENY_NODE_NAMES = ["Insert", "Update", "Delete", "Drop", "Alter", "Create", "Truncate", "Command", "Merge"]
DENY_NODES = tuple(getattr(exp, name) for name in DENY_NODE_NAMES if hasattr(exp, name))


def validate_sql(sql: str) -> ValidationResult:
    settings = get_settings()
    if ";" in sql.strip().rstrip(";"):
        return ValidationResult(ok=False, reason="Only one SQL statement is allowed.")

    try:
        parsed = sqlglot.parse_one(sql, read=settings.sql_dialect)
    except Exception as exc:
        return ValidationResult(ok=False, reason=f"SQL parse failed: {exc}")

    if parsed is None:
        return ValidationResult(ok=False, reason="Empty SQL.")

    if any(True for node_type in DENY_NODES if any(True for _ in parsed.find_all(node_type))):
        return ValidationResult(ok=False, reason="Write/DDL statements are not allowed.")

    if not isinstance(parsed, exp.Select):
        return ValidationResult(ok=False, reason="Only SELECT queries are allowed.")

    if parsed.find(exp.Star):
        return ValidationResult(ok=False, reason="SELECT * is not allowed.")

    touched_tables: list[str] = []
    for table in parsed.find_all(exp.Table):
        name = table.name
        if name not in settings.allowed_tables:
            return ValidationResult(ok=False, reason=f"Table not allowed: {name}")
        touched_tables.append(name)

    if not touched_tables:
        return ValidationResult(ok=False, reason="No allowed table detected.")

    if not parsed.args.get("limit"):
        parsed = parsed.limit(settings.max_rows)

    normalized = parsed.sql(dialect=settings.sql_dialect)
    return ValidationResult(ok=True, sql=normalized, touched_tables=list(dict.fromkeys(touched_tables)))
