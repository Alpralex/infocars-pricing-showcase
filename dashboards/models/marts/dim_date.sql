-- Daily calendar from the first ad to the snapshot date. Facts join on listed_date (and removed_date).
select
    d::date                                   as date_day,
    date_trunc('week', d)::date               as week_start,
    date_trunc('month', d)::date              as month_start,
    year(d)                                   as year_number,
    month(d)                                  as month_number,
    strftime(d, '%b')                         as month_name,
    strftime(d, '%a')                         as weekday_name,
    d::date = '{{ var("snapshot_date") }}'::date as is_snapshot
from range('2025-05-01'::date, '{{ var("snapshot_date") }}'::date + 1, interval 1 day) t(d)
