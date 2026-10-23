"""Local demo database.

Production ran on PostgreSQL (see sql/postgres). To keep this repository easy
to run, the demo loads the same shape of data into SQLite in memory.
"""

from __future__ import annotations

import csv
import sqlite3
from datetime import date
from pathlib import Path
from statistics import median

from .normalize import match_listing

SNAPSHOT_DATE = date(2025, 11, 1)  # "today" for listings that are still online

SCHEMA = """
CREATE TABLE raw_listings (
    id          INTEGER PRIMARY KEY,
    source      TEXT NOT NULL,
    title       TEXT NOT NULL,
    price_brl   REAL,
    km          INTEGER,
    state       TEXT,
    listed_at   TEXT NOT NULL,
    removed_at  TEXT
);

CREATE TABLE listings (
    id              INTEGER PRIMARY KEY REFERENCES raw_listings(id),
    make            TEXT NOT NULL,
    model           TEXT NOT NULL,
    version         TEXT NOT NULL,
    year            INTEGER NOT NULL,
    price_brl       REAL NOT NULL,
    km              INTEGER,
    state           TEXT,
    days_on_market  INTEGER NOT NULL,
    is_active       INTEGER NOT NULL,
    match_method    TEXT NOT NULL
);

CREATE VIEW market_by_version AS
SELECT make, model, version, year, state,
       COUNT(*)                     AS listings,
       ROUND(AVG(price_brl))        AS avg_price_brl,
       MIN(price_brl)               AS min_price_brl,
       MAX(price_brl)               AS max_price_brl,
       ROUND(AVG(days_on_market))   AS avg_days_on_market
FROM listings
GROUP BY make, model, version, year, state;
"""

# Ads outside these bounds are almost always typos ("R$ 8.990" for R$ 89,900) or placeholders.
MIN_PRICE, MAX_PRICE = 5_000, 1_500_000


def build_database(csv_path: str | Path) -> tuple[sqlite3.Connection, dict]:
    """Load raw ads, match them to the catalogue and return the connection plus a quality report."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)

    report = {"raw": 0, "matched": 0, "fuzzy": 0, "incomplete": 0, "bad_price": 0, "raw_model_spellings": set()}

    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            report["raw"] += 1
            conn.execute(
                "INSERT INTO raw_listings VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (row["id"], row["source"], row["title"], row["price_brl"] or None, row["km"] or None,
                 row["state"], row["listed_at"], row["removed_at"] or None),
            )
            report["raw_model_spellings"].add(_model_spelling(row["title"]))

            price = float(row["price_brl"]) if row["price_brl"] else None
            if price is None or not MIN_PRICE <= price <= MAX_PRICE:
                report["bad_price"] += 1
                continue

            match = match_listing(row["title"])
            if not match.is_complete:
                report["incomplete"] += 1
                continue

            listed = date.fromisoformat(row["listed_at"])
            removed = date.fromisoformat(row["removed_at"]) if row["removed_at"] else None
            conn.execute(
                "INSERT INTO listings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (row["id"], match.make, match.model, match.version, match.year, price,
                 int(row["km"]) if row["km"] else None, row["state"],
                 ((removed or SNAPSHOT_DATE) - listed).days, int(removed is None), match.method),
            )
            report["matched"] += 1
            report["fuzzy"] += match.method == "fuzzy"

    report["outliers"] = _drop_price_outliers(conn)
    report["matched"] -= report["outliers"]
    report["fuzzy"] = conn.execute("SELECT COUNT(*) FROM listings WHERE match_method = 'fuzzy'").fetchone()[0]
    conn.commit()
    report["raw_model_spellings"] = len(report["raw_model_spellings"])
    report["canonical_models"] = conn.execute("SELECT COUNT(DISTINCT make || model) FROM listings").fetchone()[0]
    return conn, report


def _drop_price_outliers(conn: sqlite3.Connection) -> int:
    """Remove prices far from comparable cars, such as R$ 15,715 typed for a R$ 157,150 Corolla.

    The fixed MIN_PRICE/MAX_PRICE bounds miss these because the wrong value still looks like a car price.
    """
    groups: dict[tuple, list] = {}
    for r in conn.execute("SELECT id, model, version, year, price_brl FROM listings"):
        groups.setdefault((r["model"], r["version"], r["year"]), []).append((r["id"], r["price_brl"]))

    outliers = []
    for rows in groups.values():
        if len(rows) < 3:
            continue
        mid = median(price for _, price in rows)
        outliers += [(id_,) for id_, price in rows if not 0.5 * mid <= price <= 2 * mid]
    conn.executemany("DELETE FROM listings WHERE id = ?", outliers)
    return len(outliers)


def _model_spelling(title: str) -> str:
    # The first two words of an ad are usually how the seller wrote make and model.
    return " ".join(title.lower().split()[:2])


def market_price(conn: sqlite3.Connection, model: str, version: str, year: int, state: str | None = None) -> dict:
    """Median asking price and spread for comparable listings."""
    query = "SELECT price_brl, days_on_market FROM listings WHERE model = ? AND version = ? AND year = ?"
    params: list = [model.lower(), version.lower(), year]
    if state:
        query += " AND state = ?"
        params.append(state.upper())
    rows = conn.execute(query, params).fetchall()
    if not rows:
        return {"comparables": 0}

    prices = sorted(r["price_brl"] for r in rows)
    q1, q3 = prices[len(prices) // 4], prices[(3 * len(prices)) // 4]
    return {
        "comparables": len(prices),
        "median_price_brl": round(median(prices)),
        "p25_price_brl": round(q1),
        "p75_price_brl": round(q3),
        "median_days_on_market": round(median(r["days_on_market"] for r in rows)),
    }


def price_position(conn: sqlite3.Connection, model: str, version: str, year: int, asking_price: float,
                   state: str | None = None) -> dict:
    """Where a dealer's asking price sits against the market for the same car."""
    market = market_price(conn, model, version, year, state)
    if not market["comparables"]:
        return market
    gap = asking_price - market["median_price_brl"]
    if asking_price > market["p75_price_brl"]:
        position = "above market"
    elif asking_price < market["p25_price_brl"]:
        position = "below market"
    else:
        position = "within market range"
    return {**market, "asking_price_brl": asking_price, "gap_to_median_brl": round(gap), "position": position}
