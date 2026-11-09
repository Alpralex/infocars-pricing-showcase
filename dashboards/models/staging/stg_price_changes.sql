-- One row per price change an ad made while online (data/sample_price_changes.csv): the asking price before
-- and after, and the day it changed. The listing's price in stg_raw_listings is the price after the change.
select
    listing_id::integer                 as listing_id,
    changed_at::date                    as changed_date,
    old_price_brl::double               as old_price_brl,
    new_price_brl::double               as new_price_brl,
    new_price_brl::double / old_price_brl::double - 1 as change_pct
from read_csv('{{ var("raw_path") }}/sample_price_changes.csv', header = true, all_varchar = true)
