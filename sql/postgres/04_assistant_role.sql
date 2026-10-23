-- The assistant connects with its own role. It can read the clean tables and
-- market views and nothing else, so even a query that slips past the
-- application-level checks (infocars/sql_guard.py) cannot change data or read raw ads.

CREATE ROLE assistant_readonly LOGIN PASSWORD :'assistant_password';  -- psql -v assistant_password=...

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM assistant_readonly;
GRANT USAGE ON SCHEMA public TO assistant_readonly;
GRANT SELECT ON makes, models, versions, listings, mv_market_by_version, mv_weekly_prices TO assistant_readonly;

-- Stop runaway queries written by the model.
ALTER ROLE assistant_readonly SET statement_timeout = '5s';
ALTER ROLE assistant_readonly SET default_transaction_read_only = on;
