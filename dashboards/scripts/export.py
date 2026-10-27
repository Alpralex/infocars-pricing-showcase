"""Export the marts: Parquet files for Power BI and Qlik (powerbi/data/) and compact JSON for the web page (web/data/).

Run from the dashboards folder after dbt build: python scripts/export.py
"""
import json
import os

import duckdb

DB = os.environ.get("INFOCARS_DB_PATH", "infocars.duckdb")
con = duckdb.connect(DB, read_only=True)
os.makedirs("powerbi/data", exist_ok=True)
os.makedirs("web/data", exist_ok=True)

tables = {
    "dim_date": "select * exclude (is_snapshot), is_snapshot::integer as is_snapshot from dim_date",
    "dim_version": "select * from dim_version",
    "dim_state": "select * from dim_state",
    # flags as 0/1 integers so Power BI and Qlik read them the same way
    "fct_listings": """
        select listing_id, version_key, model_year, state, source, match_method, price_brl, km,
               listed_date, removed_date, last_seen_date, days_on_market,
               is_active::integer as is_active, is_sold::integer as is_sold,
               comparables, market_p25_brl, market_median_brl, market_p75_brl,
               gap_to_median_brl, gap_to_median_pct, price_position, price_band, price_band_order
        from fct_listings order by listing_id""",
    "mart_market_by_version": "select * from mart_market_by_version order by version_key, model_year, state",
    "mart_data_quality": "select * from mart_data_quality order by step_order",
}
for name, sql in tables.items():
    con.execute(f"copy ({sql}) to 'powerbi/data/{name}.parquet' (format parquet, compression zstd)")
    n = con.execute(f"select count(*) from 'powerbi/data/{name}.parquet'").fetchone()[0]
    print(f"powerbi/data/{name}.parquet: {n:,} rows")


def rows(sql):
    return [[float(v) if hasattr(v, "as_tuple") else v for v in r] for r in con.execute(sql).fetchall()]


def dump(name, data):
    with open(f"web/data/{name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"), ensure_ascii=False)
    print(f"web/data/{name}.json: {len(data):,} rows")


# id, version key, model year, state, price, listed (YYYY-MM-DD), removed or null, days on market,
# comparables, market p25, median, p75 (null with fewer than 5 comparables), price band (1-6), source
dump("listings", rows("""
    select listing_id, version_key, model_year, state, price_brl::integer,
           strftime(listed_date, '%Y-%m-%d'), strftime(removed_date, '%Y-%m-%d'), days_on_market,
           comparables, market_p25_brl::integer, market_median_brl::integer, market_p75_brl::integer,
           price_band_order, source
    from fct_listings order by listing_id"""))

meta = {
    "versions": rows("select version_key, make_name, model_name, version_name, body_type from dim_version order by sort_order"),
    "states": rows("select state, state_name, region from dim_state order by sort_order"),
    "bands": rows("select distinct price_band_order, price_band from fct_listings order by 1"),
    "quality": rows("select step_key, step, ads from mart_data_quality order by step_order"),
    "snapshot": "2025-11-01",
    "first_day": "2025-05-01",
}
with open("web/data/meta.json", "w", encoding="utf-8") as f:
    json.dump(meta, f, separators=(",", ":"), ensure_ascii=False)
print("web/data/meta.json ok")
