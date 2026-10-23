"""Checks for SQL written by the language model before it runs.

The assistant may write its own queries, but only read-only ones and only
against the tables listed in ALLOWED_TABLES. In production this sat on top of
a PostgreSQL role with SELECT-only grants, so a query had to pass both.
"""

from __future__ import annotations

import re

ALLOWED_TABLES = {"listings", "market_by_version"}
MAX_ROWS = 200

FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|truncate|grant|revoke|attach|detach|pragma|vacuum)\b",
    re.IGNORECASE,
)
TABLE_REF = re.compile(r"\b(?:from|join)\s+([a-z_][\w.]*)", re.IGNORECASE)
CTE_NAME = re.compile(r"(?:\bwith|,)\s*([a-z_]\w*)\s+as\s*\(", re.IGNORECASE)


class SqlGuardError(ValueError):
    pass


def check_sql(sql: str) -> str:
    """Return a safe version of the query, or raise SqlGuardError explaining why it was refused."""
    query = sql.strip().rstrip(";").strip()

    if not query:
        raise SqlGuardError("Empty query.")
    if ";" in query:
        raise SqlGuardError("Only one statement is allowed.")
    if "--" in query or "/*" in query:
        raise SqlGuardError("Comments are not allowed.")
    if not re.match(r"^(select|with)\b", query, re.IGNORECASE):
        raise SqlGuardError("Only SELECT queries are allowed.")
    if FORBIDDEN.search(query):
        raise SqlGuardError("The query contains a write or admin keyword.")

    ctes = {name.lower() for name in CTE_NAME.findall(query)}
    tables = {name.lower() for name in TABLE_REF.findall(query)} - ctes
    blocked = tables - ALLOWED_TABLES
    if blocked:
        raise SqlGuardError(f"Table not allowed: {', '.join(sorted(blocked))}.")

    if not re.search(r"\blimit\s+\d+\s*$", query, re.IGNORECASE):
        query = f"{query} LIMIT {MAX_ROWS}"
    return query
