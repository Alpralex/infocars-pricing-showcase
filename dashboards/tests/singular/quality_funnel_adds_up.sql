-- Every raw ad ends in exactly one outcome: raw = clean + bad price + incomplete + outlier
-- (test_quality_report_adds_up in tests/test_market_and_assistant.py).
select *
from (
    select
        sum(ads) filter (where step_key = 'raw_ads') as raw_ads,
        sum(ads) filter (where step_key in ('clean_ads', 'bad_price', 'incomplete', 'price_outlier')) as outcomes
    from {{ ref('mart_data_quality') }}
) t
where raw_ads <> outcomes
