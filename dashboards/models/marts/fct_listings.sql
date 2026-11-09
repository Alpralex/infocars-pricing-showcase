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
        quantile_cont(b.price_brl, 0.75)                     as market_p75_brl,
        quantile_cont(b.km, 0.50)                            as market_median_km
    from kept a
    left join kept b
      on b.version_key = a.version_key and b.model_year = a.model_year and b.listing_id <> a.listing_id
    group by a.listing_id
),
compared as (
    select
        k.listing_id, k.version_key, k.model_year, k.state, k.city, k.source, k.match_method,
        k.seller_type, k.transmission, k.fuel, k.colour, k.photos,
        k.price_brl, k.km, k.listed_date, k.removed_date, k.last_seen_date, k.days_on_market,
        k.is_active, not k.is_active as is_sold,
        -- mileage bands as the production dashboard showed them
        case when k.km < 10000 then 1 when k.km < 30000 then 2 when k.km < 50000 then 3 when k.km < 100000 then 4 else 5 end as km_band_order,
        case when k.km < 10000 then 'Under 10k km' when k.km < 30000 then '10-30k km' when k.km < 50000 then '30-50k km'
             when k.km < 100000 then '50-100k km' else 'Over 100k km' end as km_band,
        -- the other price drivers as the dashboards label them, so every tool groups the same way
        case k.seller_type when 'private' then 'Private seller' else 'Dealer' end          as seller_label,
        case k.transmission when 'automatic' then 'Automatic' else 'Manual' end           as gearbox_label,
        case k.fuel when 'flex' then 'Flex' when 'petrol' then 'Petrol' else 'Hybrid' end  as fuel_label,
        case when k.photos < 8 then 1 when k.photos < 16 then 2 else 3 end                 as photos_band_order,
        case when k.photos < 8 then 'Under 8 photos' when k.photos < 16 then '8-15 photos' else '16 or more' end
                                                                                           as photos_band,
        c.changed_date                                          as price_cut_date,
        c.old_price_brl                                         as price_before_cut_brl,
        c.change_pct                                            as price_cut_pct,
        c.listing_id is not null                                as had_price_cut,
        m.comparables,
        case when m.comparables >= {{ var("min_comparables") }} then round(m.market_median_km) end   as market_median_km,
        case when m.comparables >= {{ var("min_comparables") }} then round(m.market_p25_brl) end    as market_p25_brl,
        case when m.comparables >= {{ var("min_comparables") }} then round(m.market_median_brl) end as market_median_brl,
        case when m.comparables >= {{ var("min_comparables") }} then round(m.market_p75_brl) end    as market_p75_brl
    from kept k
    join market m using (listing_id)
    left join {{ ref('stg_price_changes') }} c using (listing_id)
),
banded as (
select
    *,
    price_brl - market_median_brl                            as gap_to_median_brl,
    price_brl / market_median_brl - 1                        as gap_to_median_pct,
    km - market_median_km                                    as km_vs_market,
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
