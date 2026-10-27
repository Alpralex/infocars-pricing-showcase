-- Catalogue match per ad, from the repository's Python matcher (seeds/listing_matches.csv).
select
    listing_id,
    nullif(make, '')                    as make,
    nullif(model, '')                   as model,
    nullif(version, '')                 as version,
    model_year,
    match_method,
    title_spelling,
    case when model is not null and version is not null then model || '|' || version end as version_key,
    -- a match is complete with make, model, version and year (Match.is_complete in normalize.py)
    (make is not null and model is not null and version is not null and model_year is not null) as is_complete
from {{ ref('listing_matches') }}
