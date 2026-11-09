-- The risk score is the sum of its three parts, each within its weight, and the band follows the score.
select listing_id
from {{ ref('mart_stock_risk') }}
where risk_score <> price_points + time_points + mileage_points
   or price_points not between 0 and 50 or time_points not between 0 and 30 or mileage_points not between 0 and 20
   or (risk_band = 'High' and risk_score < 60) or (risk_band = 'Low' and risk_score >= 35)
   or (risk_band = 'Medium' and risk_score not between 35 and 59)
