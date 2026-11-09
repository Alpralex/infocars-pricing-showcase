-- How fast the stock turns: the share of ads still online after 0, 7, 14, ... 90 days, per model and for all
-- models (model_name = 'All models'), over the cohort of clean ads listed at least 90 days before the snapshot,
-- so every ad in the curve could be followed for the whole 90 days and the share never rises. The production
-- LiquidityFunnel drew the same curve day by day; here the days are fixed so the three dashboards draw the same points.
with days(day) as (select unnest([0, 7, 14, 21, 30, 45, 60, 90])),
ads as (
    select l.listing_id, v.model_name, l.listed_date, l.removed_date, l.days_on_market, l.price_position
    from {{ ref('fct_listings') }} l
    join {{ ref('dim_version') }} v using (version_key)
    where l.listed_date <= '{{ var("snapshot_date") }}'::date - interval 90 days
),
groups as (
    select model_name as group_name, 2 as group_order, * from ads
    union all
    select 'All models', 1, * from ads
),
points as (
    select
        g.group_name,
        g.group_order,
        d.day,
        count(*)                                                                   as ads_observed,
        count(*) filter (where g.removed_date is null or g.removed_date > g.listed_date + d.day)
                                                                                   as still_online,
        count(*) filter (where g.removed_date is not null and g.removed_date <= g.listed_date + d.day)
                                                                                   as sold_by_day
    from groups g
    cross join days d
    group by all
)
select
    group_name,
    group_order,
    day,
    ads_observed,
    still_online,
    sold_by_day,
    still_online / ads_observed                                                    as still_online_share,
    sold_by_day / ads_observed                                                     as sold_share
from points
