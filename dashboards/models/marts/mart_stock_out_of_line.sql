-- Stock to review: ads still online on the snapshot date whose asking price sits outside the
-- 25th-75th percentile of comparable ads (price_position() in infocars/db.py).
select
    l.listing_id,
    v.car_name,
    v.make_name,
    l.model_year,
    l.state,
    l.source,
    l.price_brl,
    l.market_p25_brl,
    l.market_median_brl,
    l.market_p75_brl,
    l.comparables,
    l.gap_to_median_brl,
    l.gap_to_median_pct,
    l.price_position,
    l.days_on_market                                                   as days_online
from {{ ref('fct_listings') }} l
join {{ ref('dim_version') }} v using (version_key)
where l.is_active and l.price_position in ('above market', 'below market')
