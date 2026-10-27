-- Does the asking price change how fast a car sells? One row per price band
-- (asking price against the median of comparable ads). Days to sell count sold ads only
-- (an ad that disappears is treated as sold); the share still online shows the ads not yet sold.
select
    price_band_order,
    price_band,
    count(*)                                                           as listings,
    count(*) filter (where is_sold)                                    as sold_listings,
    count(*) filter (where is_active)                                  as active_listings,
    count(*) filter (where is_active) / count(*)                       as still_online_share,
    quantile_cont(days_on_market, 0.50) filter (where is_sold)         as median_days_to_sell,
    avg(days_on_market) filter (where is_sold)                         as avg_days_to_sell,
    count(*) filter (where is_sold and days_on_market <= 30)
        / nullif(count(*) filter (where is_sold), 0)                   as sold_within_30d_share,
    median(gap_to_median_pct)                                          as median_gap_pct
from {{ ref('fct_listings') }}
group by all
