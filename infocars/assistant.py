"""Pricing assistant on the Anthropic Claude API.

The model never sees the database directly. It gets three tools:

- market_price: median price and spread for a make/model/version/year.
- price_position: where a dealer's asking price sits against that market.
- run_sql: free-form read-only SQL, checked by sql_guard before it runs.

The system prompt and tool definitions are marked for prompt caching. They are
the same on every request, so after the first call they are read from cache,
which cuts cost and latency.
"""

from __future__ import annotations

import json
import os
import sqlite3

from .db import market_price, price_position
from .sql_guard import SqlGuardError, check_sql

MODEL = os.environ.get("INFOCARS_MODEL", "claude-sonnet-5-5")
MAX_TOOL_ROUNDS = 5

SYSTEM_PROMPT = """You help used-car dealers in Brazil price their stock.
Answer in the dealer's language. Base every number on a tool result and say how many comparable listings it came from.
If there are fewer than 5 comparables, say the estimate is weak.
Never invent prices. If the tools return nothing, say so.
Prices are asking prices in Brazilian reais (BRL), not sale prices.
Model names are lowercase in the database, e.g. model "onix", version "ltz"."""

TOOLS = [
    {
        "name": "market_price",
        "description": "Median asking price, 25th and 75th percentile and median days on market for comparable listings.",
        "input_schema": {
            "type": "object",
            "properties": {
                "model": {"type": "string", "description": "Canonical model, e.g. onix"},
                "version": {"type": "string", "description": "Canonical version, e.g. ltz"},
                "year": {"type": "integer", "description": "Model year"},
                "state": {"type": "string", "description": "Optional two-letter Brazilian state, e.g. SP"},
            },
            "required": ["model", "version", "year"],
        },
    },
    {
        "name": "price_position",
        "description": "Compare a dealer's asking price with the market for the same car.",
        "input_schema": {
            "type": "object",
            "properties": {
                "model": {"type": "string"},
                "version": {"type": "string"},
                "year": {"type": "integer"},
                "asking_price": {"type": "number", "description": "Dealer's asking price in BRL"},
                "state": {"type": "string"},
            },
            "required": ["model", "version", "year", "asking_price"],
        },
    },
    {
        "name": "run_sql",
        "description": (
            "Run one read-only SQLite SELECT for questions the other tools cannot answer. "
            "Tables: listings(make, model, version, year, price_brl, km, state, days_on_market, is_active), "
            "market_by_version(make, model, version, year, state, listings, avg_price_brl, min_price_brl, "
            "max_price_brl, avg_days_on_market)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"sql": {"type": "string"}},
            "required": ["sql"],
        },
        "cache_control": {"type": "ephemeral"},  # caches every tool definition up to here
    },
]


def run_tool(conn: sqlite3.Connection, name: str, args: dict) -> dict:
    if name == "market_price":
        return market_price(conn, args["model"], args["version"], args["year"], args.get("state"))
    if name == "price_position":
        return price_position(conn, args["model"], args["version"], args["year"], args["asking_price"],
                              args.get("state"))
    if name == "run_sql":
        try:
            query = check_sql(args["sql"])
        except SqlGuardError as e:
            return {"error": f"Query refused: {e}"}
        rows = conn.execute(query).fetchall()
        return {"rows": [dict(r) for r in rows]}
    return {"error": f"Unknown tool: {name}"}


def ask(question: str, conn: sqlite3.Connection, client=None) -> str:
    """Answer one question, letting the model call tools until it has what it needs."""
    if client is None:
        import anthropic
        client = anthropic.Anthropic()

    messages = [{"role": "user", "content": question}]
    for _ in range(MAX_TOOL_ROUNDS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            tools=TOOLS,
            messages=messages,
        )
        if response.stop_reason != "tool_use":
            return "".join(block.text for block in response.content if block.type == "text")

        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in response.content:
            if block.type == "tool_use":
                output = run_tool(conn, block.name, block.input)
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(output)})
        messages.append({"role": "user", "content": results})

    return "I could not finish this answer within the tool-call limit. Try a more specific question."
