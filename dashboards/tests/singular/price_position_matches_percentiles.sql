-- price_position follows price_position() in infocars/db.py, and a market needs enough comparables.
select listing_id
from {{ ref('fct_listings') }}
where (price_position = 'above market' and not price_brl > market_p75_brl)
   or (price_position = 'below market' and not price_brl < market_p25_brl)
   or (price_position = 'within market range' and not price_brl between market_p25_brl and market_p75_brl)
   or (price_position = 'too few comparables' and comparables >= {{ var("min_comparables") }})
   or (price_position <> 'too few comparables' and comparables < {{ var("min_comparables") }})
