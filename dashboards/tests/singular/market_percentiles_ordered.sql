-- p25 <= median <= p75 wherever a market exists (test_market_price in the Python tests).
select listing_id, market_p25_brl, market_median_brl, market_p75_brl
from {{ ref('fct_listings') }}
where market_median_brl is not null
  and not (market_p25_brl <= market_median_brl and market_median_brl <= market_p75_brl)
union all
select null, p25_price_brl, median_price_brl, p75_price_brl
from {{ ref('mart_market_by_version') }}
where not (p25_price_brl <= median_price_brl and median_price_brl <= p75_price_brl)
