-- The buy list follows its own rules: every ad is from a private seller, still online, at or below the comparable
-- median; the class matches the gap; the expected margin is the median less the asking price less 2% preparation;
-- and the offer never exceeds the asking price.
select listing_id
from {{ ref('mart_buy_list') }}
where price_brl > market_median_brl
   or (buy_class = 'Buy now' and gap_to_median_pct > -0.08)
   or (buy_class = 'Negotiate' and (gap_to_median_pct <= -0.08 or gap_to_median_pct > -0.03))
   or (buy_class = 'Wait' and gap_to_median_pct <= -0.03)
   or abs(expected_margin_brl - round(market_median_brl - price_brl - 0.02 * market_median_brl)) > 1
   or least(price_brl, target_offer_brl) > price_brl
   or priority_score not between 0 and 100
