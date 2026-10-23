-- Production-style schema for PostgreSQL.
-- Raw ads land in raw_listings exactly as collected. The catalogue tables hold
-- canonical makes, models and versions, and listings links each ad to them.
-- Keeping raw and clean data apart means matching can be re-run and audited.

CREATE TABLE makes (
    make_id   SMALLSERIAL PRIMARY KEY,
    name      TEXT NOT NULL UNIQUE
);

CREATE TABLE models (
    model_id  SERIAL PRIMARY KEY,
    make_id   SMALLINT NOT NULL REFERENCES makes,
    name      TEXT NOT NULL,
    UNIQUE (make_id, name)
);

CREATE TABLE versions (
    version_id  SERIAL PRIMARY KEY,
    model_id    INT NOT NULL REFERENCES models,
    name        TEXT NOT NULL,
    UNIQUE (model_id, name)
);

-- Every spelling seen in ads that maps to a canonical model or version.
CREATE TABLE aliases (
    alias       TEXT NOT NULL,
    model_id    INT REFERENCES models,
    version_id  INT REFERENCES versions,
    CHECK (num_nonnulls(model_id, version_id) = 1)
);
CREATE UNIQUE INDEX aliases_model_uq ON aliases (alias, model_id) WHERE model_id IS NOT NULL;
CREATE UNIQUE INDEX aliases_version_uq ON aliases (alias, version_id) WHERE version_id IS NOT NULL;

CREATE TABLE raw_listings (
    listing_id   BIGSERIAL PRIMARY KEY,
    source       TEXT NOT NULL,
    url          TEXT NOT NULL UNIQUE,
    title        TEXT NOT NULL,
    price_text   TEXT,
    km_text      TEXT,
    state        CHAR(2),
    city         TEXT,
    first_seen   DATE NOT NULL,
    last_seen    DATE NOT NULL,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TYPE listing_status AS ENUM ('active', 'removed');

CREATE TABLE listings (
    listing_id     BIGINT PRIMARY KEY REFERENCES raw_listings,
    version_id     INT NOT NULL REFERENCES versions,
    model_year     SMALLINT NOT NULL CHECK (model_year BETWEEN 1980 AND 2030),
    price_brl      NUMERIC(12, 2) NOT NULL CHECK (price_brl BETWEEN 5000 AND 1500000),
    km             INT CHECK (km BETWEEN 0 AND 1500000),
    state          CHAR(2),
    status         listing_status NOT NULL,
    first_seen     DATE NOT NULL,
    last_seen      DATE NOT NULL,
    -- A listing that disappears from the site is treated as sold on its last day online.
    days_on_market INT GENERATED ALWAYS AS (last_seen - first_seen) STORED,
    match_method   TEXT NOT NULL CHECK (match_method IN ('exact', 'fuzzy', 'manual'))
);

-- Most queries ask for one version and year, often for active ads only.
CREATE INDEX listings_version_year_idx ON listings (version_id, model_year);
CREATE INDEX listings_active_idx ON listings (version_id, model_year, state) WHERE status = 'active';
-- Dates only grow, so a BRIN index is small and enough for range scans.
CREATE INDEX listings_last_seen_brin ON listings USING brin (last_seen);
