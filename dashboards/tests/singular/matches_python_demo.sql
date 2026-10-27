-- The SQL quality checks reproduce the Python demo (python scripts/demo.py):
-- 1,200 raw ads, 15 bad prices, 18 outliers, 1,167 clean of which 187 by typo correction,
-- 116 spellings to 7 models, and a 2023 Onix LTZ market of 6 ads with a median of R$ 68,400.
with q as (select step_key, ads from {{ ref('mart_data_quality') }}),
expected(step_key, ads) as (
    values ('raw_ads', 1200), ('bad_price', 15), ('incomplete', 0), ('price_outlier', 18), ('clean_ads', 1167),
           ('fuzzy_matched', 187), ('title_spellings', 116), ('canonical_models', 7)
)
select e.step_key, e.ads as expected, q.ads as actual
from expected e left join q using (step_key)
where q.ads is distinct from e.ads
union all
select 'onix ltz 2023', 6 * 1000000 + 68400, count(*) * 1000000 + median(price_brl)
from {{ ref('fct_listings') }}
where version_key = 'onix|ltz' and model_year = 2023
having count(*) <> 6 or median(price_brl) <> 68400
