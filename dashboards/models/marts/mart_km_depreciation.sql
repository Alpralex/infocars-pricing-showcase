-- How much the asking price falls per 10,000 km, per version: the production km_price_analyzer as SQL.
-- The slope comes from a least-squares fit of price on km inside each version and model year (same car, same
-- age, so the slope is the kilometres alone), over groups of {{ var("min_regression_ads") }} or more clean ads,
-- then pooled per version weighting each year's slope by its number of ads.
with by_year as (
    select
        version_key,
        model_year,
        count(*)                                   as ads,
        median(price_brl)                          as median_price_brl,
        median(km)                                 as median_km,
        regr_slope(price_brl, km)                  as slope_per_km,
        regr_r2(price_brl, km)                     as r2
    from {{ ref('fct_listings') }}
    group by all
    having count(*) >= {{ var("min_regression_ads") }}
)
select
    v.car_name,
    v.make_name,
    v.model_name,
    b.version_key,
    sum(b.ads)                                                        as ads,
    count(*)                                                          as model_years,
    round(sum(b.median_price_brl * b.ads) / sum(b.ads))               as median_price_brl,
    round(sum(b.slope_per_km * b.ads) / sum(b.ads) * 10000)           as loss_per_10k_km_brl,
    sum(b.slope_per_km * b.ads) / sum(b.ads) * 10000
        / (sum(b.median_price_brl * b.ads) / sum(b.ads))              as loss_per_10k_km_pct,
    sum(b.r2 * b.ads) / sum(b.ads)                                    as r2
from by_year b
join {{ ref('dim_version') }} v using (version_key)
group by all
