-- The quality report of scripts/demo.py as a table: how many raw ads reach the market statistics.
with s as (select * from {{ ref('stg_listings_screened') }})
select * from (values
    (1, 'raw_ads',          'Raw ads collected',                       (select count(*) from s)),
    (2, 'bad_price',        'Dropped: price missing or out of range',  (select count(*) from s where quality_status = 'bad_price')),
    (3, 'incomplete',       'Dropped: no full catalogue match',        (select count(*) from s where quality_status = 'incomplete')),
    (4, 'price_outlier',    'Dropped: price far from comparable cars', (select count(*) from s where quality_status = 'price_outlier')),
    (5, 'clean_ads',        'Clean ads matched to the catalogue',      (select count(*) from s where quality_status = 'kept')),
    (6, 'fuzzy_matched',    'Clean ads matched through typo correction', (select count(*) from s where quality_status = 'kept' and match_method = 'fuzzy')),
    (7, 'title_spellings',  'Make and model spellings in raw titles',  (select count(distinct title_spelling) from s)),
    (8, 'canonical_models', 'Canonical models after matching',         (select count(distinct make || model) from s where quality_status = 'kept'))
) t(step_order, step_key, step, ads)
