-- One row per clean ad (quality_status = 'kept'), compared with the market for the same car.
-- The market for an ad is every other clean ad of the same version and model year in all states
-- (market_price() in infocars/db.py without a state), so an ad never counts as its own comparable.
-- Percentiles use percentile_cont, as the production view (sql/postgres/02_market_views.sql).
-- Position follows price_position(): above the 75th percentile is above market, below the 25th is below.
with kept as (
    select * from {{ ref('stg_listings_screened') }} where quality_status = 'kept'
),
market as (
    select
        a.listing_id,
        count(b.listing_id)                                  as comparables,
        quantile_cont(b.price_brl, 0.25)                     as market_p25_brl,
        quantile_cont(b.price_brl, 0.50)                     as market_median_brl,
        quantile_cont(b.price_brl, 0.75)                     as market_p75_brl
    from kept a
    left join kept b
      on b.version_key = a.version_key and b.model_year = a.model_year and b.listing_id <> a.listing_id
    group by a.listing_id
),
compared as (
    select
        k.listing_id, k.version_key, k.model_year, k.state, k.source, k.match_method,
        k.price_brl, k.km, k.listed_date, k.removed_date, k.last_seen_date, k.days_on_market,
        k.is_active, not k.is_active as is_sold,
        m.comparables,
        case when m.comparables >= {{ var("min_comparables") }} then round(m.market_p25_brl) end    as market_p25_brl,
        case when m.comparables >= {{ var("min_comparables") }} then round(m.market_median_brl) end as market_median_brl,
        case when m.comparables >= {{ var("min_comparables") }} then round(m.market_p75_brl) end    as market_p75_brl
    from kept k
    join market m using (listing_id)
),
banded as (
select
    *,
    price_brl - market_median_brl                            as gap_to_median_brl,
    price_brl / market_median_brl - 1                        as gap_to_median_pct,
    case
        when market_median_brl is null then 'too few comparables'
        when price_brl > market_p75_brl then 'above market'
        when price_brl < market_p25_brl then 'below market'
        else 'within market range'
    end                                                      as price_position,
    -- asking price against the median of comparable ads, in five bands
    case
        when market_median_brl is null then 6
        when price_brl / market_median_brl - 1 < -0.06 then 1
        when price_brl / market_median_brl - 1 < -0.02 then 2
        when price_brl / market_median_brl - 1 <= 0.02 then 3
        when price_brl / market_median_brl - 1 <= 0.06 then 4
        else 5
    end                                                      as price_band_order
from compared
)
select
    *,
    case price_band_order
        when 1 then 'Below -6%' when 2 then '-6% to -2%' when 3 then '-2% to +2%'
        when 4 then '+2% to +6%' when 5 then 'Above +6%' else 'Too few comparables'
    end as price_band
from banded
