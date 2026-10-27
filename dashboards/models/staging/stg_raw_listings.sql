-- One row per ad exactly as collected (data/sample_listings.csv). Empty strings become nulls.
select
    id::integer                         as listing_id,
    source,
    title,
    nullif(price_brl, '')::double       as price_brl,
    nullif(km, '')::integer             as km,
    nullif(state, '')                   as state,
    listed_at::date                     as listed_date,
    nullif(removed_at, '')::date        as removed_date
from read_csv('{{ var("raw_path") }}/sample_listings.csv', header = true, all_varchar = true)
