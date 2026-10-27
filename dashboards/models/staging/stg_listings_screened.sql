-- Every raw ad with its quality outcome, in the order infocars/db.py applies the checks:
--   1. bad_price      price missing or outside {{ var("min_price_brl") }}..{{ var("max_price_brl") }} BRL
--   2. incomplete     no full catalogue match (make, model, version, year)
--   3. price_outlier  outside 0.5x-2x of the median of the same model, version and year (groups of 3 or more),
--                     usually a price typed without its last digit
--   4. kept
-- An ad that disappears is treated as sold on its last day online; ads still online are measured to the snapshot.
with joined as (
    select
        r.*,
        m.make, m.model, m.version, m.version_key, m.model_year, m.match_method, m.title_spelling, m.is_complete,
        r.price_brl is null
            or r.price_brl not between {{ var("min_price_brl") }} and {{ var("max_price_brl") }} as is_bad_price
    from {{ ref('stg_raw_listings') }} r
    join {{ ref('stg_listing_matches') }} m using (listing_id)
),
peers as (
    select *,
           count(*)          over w as peer_count,
           median(price_brl) over w as peer_median_brl
    from joined
    where not is_bad_price and is_complete
    window w as (partition by model, version, model_year)
)
select
    j.listing_id, j.source, j.title, j.title_spelling, j.price_brl, j.km, j.state,
    j.make, j.model, j.version, j.version_key, j.model_year, j.match_method,
    j.listed_date, j.removed_date,
    coalesce(j.removed_date, '{{ var("snapshot_date") }}'::date) as last_seen_date,
    (coalesce(j.removed_date, '{{ var("snapshot_date") }}'::date) - j.listed_date)::integer as days_on_market,
    j.removed_date is null as is_active,
    case
        when j.is_bad_price then 'bad_price'
        when not j.is_complete then 'incomplete'
        when p.peer_count >= 3 and j.price_brl not between 0.5 * p.peer_median_brl and 2 * p.peer_median_brl
            then 'price_outlier'
        else 'kept'
    end as quality_status
from joined j
left join peers p using (listing_id)
