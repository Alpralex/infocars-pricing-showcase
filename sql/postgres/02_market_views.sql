-- Market statistics used by the dashboards and the assistant.
-- Materialised so a dealer's question does not scan every listing.
-- Refresh after each collection run: REFRESH MATERIALIZED VIEW CONCURRENTLY mv_market_by_version;

CREATE MATERIALIZED VIEW mv_market_by_version AS
SELECT
    mk.name                                                       AS make,
    md.name                                                       AS model,
    v.name                                                        AS version,
    l.model_year,
    l.state,
    COUNT(*)                                                      AS listings,
    COUNT(*) FILTER (WHERE l.status = 'active')                   AS active_listings,
    percentile_cont(0.25) WITHIN GROUP (ORDER BY l.price_brl)     AS p25_price_brl,
    percentile_cont(0.50) WITHIN GROUP (ORDER BY l.price_brl)     AS median_price_brl,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY l.price_brl)     AS p75_price_brl,
    percentile_cont(0.50) WITHIN GROUP (ORDER BY l.days_on_market)
        FILTER (WHERE l.status = 'removed')                       AS median_days_to_sell
FROM listings l
JOIN versions v  USING (version_id)
JOIN models md   USING (model_id)
JOIN makes mk    USING (make_id)
WHERE l.last_seen >= current_date - INTERVAL '180 days'
GROUP BY mk.name, md.name, v.name, l.model_year, l.state;

-- CONCURRENTLY needs a unique index. COALESCE keeps rows with no state unique too.
CREATE UNIQUE INDEX mv_market_by_version_uq
    ON mv_market_by_version (make, model, version, model_year, COALESCE(state, '--'));

-- Price history: one row per version, year and week, for trend charts.
CREATE MATERIALIZED VIEW mv_weekly_prices AS
SELECT
    version_id,
    model_year,
    date_trunc('week', last_seen)::date                       AS week,
    COUNT(*)                                                  AS listings,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY price_brl)    AS median_price_brl
FROM listings
GROUP BY version_id, model_year, date_trunc('week', last_seen);

CREATE UNIQUE INDEX mv_weekly_prices_uq ON mv_weekly_prices (version_id, model_year, week);
