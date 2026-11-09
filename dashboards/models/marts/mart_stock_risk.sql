-- Risk that an ad still online gets stuck: a 0-100 score per active ad with a market, and the weight of each
-- factor, so the score can be explained ("price 40 of 50, time 18 of 30, mileage 6 of 20"). The production
-- specification asked for this gauge with its explanation; it was never built there.
--   price   up to 50 points: how far the asking price sits above the comparable median, full at +15%
--   time    up to 30 points: days online, full at 90 days
--   mileage up to 20 points: kilometres above the comparable median, full at +50%
select
    l.listing_id,
    l.version_key,
    v.car_name,
    v.model_name,
    l.model_year,
    l.state,
    l.city,
    l.seller_type,
    l.km,
    l.market_median_km,
    l.days_on_market,
    l.price_brl,
    l.market_median_brl,
    l.market_p75_brl,
    l.gap_to_median_brl,
    l.gap_to_median_pct,
    l.price_position,
    round(50 * least(1, greatest(0, l.gap_to_median_pct / 0.15)))                            as price_points,
    round(30 * least(1, l.days_on_market / 90.0))                                            as time_points,
    round(20 * least(1, greatest(0, l.km_vs_market / nullif(l.market_median_km, 0) / 0.5)))  as mileage_points,
    round(50 * least(1, greatest(0, l.gap_to_median_pct / 0.15)))
      + round(30 * least(1, l.days_on_market / 90.0))
      + round(20 * least(1, greatest(0, l.km_vs_market / nullif(l.market_median_km, 0) / 0.5))) as risk_score,
    case
        when round(50 * least(1, greatest(0, l.gap_to_median_pct / 0.15)))
           + round(30 * least(1, l.days_on_market / 90.0))
           + round(20 * least(1, greatest(0, l.km_vs_market / nullif(l.market_median_km, 0) / 0.5))) >= 60 then 'High'
        when round(50 * least(1, greatest(0, l.gap_to_median_pct / 0.15)))
           + round(30 * least(1, l.days_on_market / 90.0))
           + round(20 * least(1, greatest(0, l.km_vs_market / nullif(l.market_median_km, 0) / 0.5))) >= 35 then 'Medium'
        else 'Low'
    end                                                                                      as risk_band,
    -- the cut that would bring the ad back to the 75th percentile, when it is above it
    case when l.price_brl > l.market_p75_brl then round(l.price_brl - l.market_p75_brl) end  as cut_to_range_brl
from {{ ref('fct_listings') }} l
join {{ ref('dim_version') }} v using (version_key)
where l.is_active and l.market_median_brl is not null
