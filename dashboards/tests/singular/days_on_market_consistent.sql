-- Sold ads count the days to their last day online; active ads count to the snapshot date.
select listing_id
from {{ ref('fct_listings') }}
where days_on_market < 0
   or days_on_market <> (coalesce(removed_date, '{{ var("snapshot_date") }}'::date) - listed_date)
   or is_active = is_sold
   or (is_sold and removed_date is null)
