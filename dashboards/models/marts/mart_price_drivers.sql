-- What moves an ad's price against its market: one row per factor and level, with the median gap to the
-- comparable median (same version and model year, so the car and its age are already held constant).
-- The web page reads this; Power BI uses it as the axis and recomputes the medians from fct_listings so slicers apply; the factors are the columns the
-- production table had (gearbox, seller account, colour, fuel, photos) plus the mileage bands.
with ads as (
    select * from {{ ref('fct_listings') }} where market_median_brl is not null
),
long as (
    select 'Mileage'      as factor, 1 as factor_order, km_band as level, km_band_order as level_order, * from ads
    union all
    select 'Seller',      2, seller_label, case seller_type when 'private' then 1 else 2 end, * from ads
    union all
    select 'Gearbox',     3, gearbox_label, case transmission when 'automatic' then 1 else 2 end, * from ads
    union all
    select 'Fuel',        4, fuel_label, case fuel when 'flex' then 1 when 'petrol' then 2 else 3 end, * from ads
    union all
    select 'Colour',      5, colour, case colour when 'White' then 1 when 'Silver' then 2 when 'Black' then 3
                                             when 'Grey' then 4 when 'Red' then 5 else 6 end, * from ads
    union all
    select 'Photos',      6, photos_band, photos_band_order, * from ads
)
select
    factor,
    factor_order,
    level,
    level_order,
    count(*)                                                       as ads,
    median(gap_to_median_pct)                                      as median_gap_pct,
    round(median(gap_to_median_brl))                               as median_gap_brl,
    count(*) filter (where price_position = 'above market') / count(*) as above_market_share,
    count(*) filter (where price_position = 'below market') / count(*) as below_market_share,
    quantile_cont(days_on_market, 0.5) filter (where is_sold)      as median_days_to_sell
from long
group by all
