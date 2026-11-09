-- Fewer ads are still online as the days pass: the share at each day is never above the share at the day before,
-- every share is between 0 and 1, and online plus sold is the cohort (day 0 is under 100% only by the ads
-- that left the site on the day they were listed).
with c as (
    select *, lag(still_online_share) over (partition by group_name order by day) as previous_share
    from {{ ref('mart_liquidity_curve') }}
)
select group_name, day
from c
where still_online_share not between 0 and 1
   or still_online_share > previous_share
   or still_online + sold_by_day <> ads_observed
