-- A price cut lowers the price, happens while the ad is online, and the price after it is the listing's price.
select c.listing_id
from {{ ref('stg_price_changes') }} c
join {{ ref('stg_raw_listings') }} r using (listing_id)
where c.new_price_brl >= c.old_price_brl
   or c.changed_date <= r.listed_date
   or (r.removed_date is not null and c.changed_date >= r.removed_date)
   or c.new_price_brl <> r.price_brl
