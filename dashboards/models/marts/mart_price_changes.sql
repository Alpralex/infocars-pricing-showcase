-- Did cutting the price work? One row per clean ad with a market, in two groups: ads that cut their price once
-- while online (data/sample_price_changes.csv) and ads that never did. For the cut ads the row carries where the
-- ad stood before and after the cut and how many days it took to sell after cutting. Sold ads only have days to
-- sell; ads still online count in still_online. The production PriceChangeAnalysis showed the same comparison.
select
    l.listing_id,
    l.version_key,
    v.car_name,
    l.model_year,
    l.state,
    l.seller_type,
    l.is_sold,
    l.is_active,
    l.listed_date,
    l.removed_date,
    l.days_on_market,
    l.had_price_cut,
    case when l.had_price_cut then 'Cut the price' else 'Never cut' end          as cut_group,
    l.price_cut_date,
    l.price_before_cut_brl,
    l.price_brl                                                                  as price_after_cut_brl,
    l.price_cut_pct,
    round(l.price_before_cut_brl - l.price_brl)                                  as cut_brl,
    case when l.had_price_cut then (l.price_cut_date - l.listed_date)::integer end as days_before_cut,
    case when l.had_price_cut then (l.last_seen_date - l.price_cut_date)::integer end as days_after_cut,
    l.market_median_brl,
    l.market_p75_brl,
    case when l.had_price_cut then l.price_before_cut_brl / l.market_median_brl - 1 end as gap_before_cut_pct,
    l.gap_to_median_pct                                                          as gap_after_cut_pct,
    case
        when not l.had_price_cut then null
        when l.price_before_cut_brl > l.market_p75_brl then 'above market'
        when l.price_before_cut_brl < l.market_p25_brl then 'below market'
        else 'within market range'
    end                                                                          as position_before_cut,
    l.price_position                                                             as position_after_cut,
    l.had_price_cut and l.price_before_cut_brl > l.market_p75_brl and l.price_brl <= l.market_p75_brl
                                                                                 as cut_brought_into_range
from {{ ref('fct_listings') }} l
join {{ ref('dim_version') }} v using (version_key)
where l.market_median_brl is not null
