-- Port of mv_market_by_version (sql/postgres/02_market_views.sql) to DuckDB:
-- per version, model year and state, the asking-price spread and median days to sell.
-- current_date is replaced by the snapshot date so the numbers do not change over time.
select
    v.make_name                                                        as make,
    v.model_name                                                       as model,
    v.version_name                                                     as version,
    l.version_key,
    l.model_year,
    l.state,
    count(*)                                                           as listings,
    count(*) filter (where l.is_active)                                as active_listings,
    quantile_cont(l.price_brl, 0.25)                                   as p25_price_brl,
    quantile_cont(l.price_brl, 0.50)                                   as median_price_brl,
    quantile_cont(l.price_brl, 0.75)                                   as p75_price_brl,
    quantile_cont(l.days_on_market, 0.50) filter (where l.is_sold)     as median_days_to_sell
from {{ ref('fct_listings') }} l
join {{ ref('dim_version') }} v using (version_key)
where l.last_seen_date >= '{{ var("snapshot_date") }}'::date - interval 180 days
group by all
