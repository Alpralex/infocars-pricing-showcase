-- The list a dealer's buyer would open every morning: ads from private sellers still online on the snapshot date,
-- asked at or below the median of comparable ads, with the margin a dealer could expect and a class
-- (Buy now, Negotiate, Wait). This is the production WhatsApp "oportunidades" query (ads well under the
-- average of the same model and year) with the dealer pricing rule from the depreciation methodology:
-- a dealer pays about 90% of the market price, and preparation costs about 2% of it.
--   expected margin  = resale at the comparable median - asking price - preparation (2% of the median)
--   target offer     = 90% of the comparable median, or the asking price when that is already lower
--   Buy now          asked 8% or more under the median (the P25 or lower, in practice)
--   Negotiate        3% to 8% under: the margin is there once the seller moves to the target offer
--   Wait             under the median by less than 3%: watch it, no margin yet
with candidates as (
    select
        l.*,
        v.car_name,
        v.make_name,
        v.model_name,
        v.body_type,
        s.state_name,
        s.region,
        round(0.90 * market_median_brl)                                    as target_offer_brl,
        round(market_median_brl - price_brl - 0.02 * market_median_brl)    as expected_margin_brl,
        round(market_median_brl - least(price_brl, 0.90 * market_median_brl) - 0.02 * market_median_brl)
                                                                            as margin_at_target_brl
    from {{ ref('fct_listings') }} l
    join {{ ref('dim_version') }} v using (version_key)
    join {{ ref('dim_state') }} s using (state)
    where l.is_active
      and l.seller_type = 'private'
      and l.market_median_brl is not null
      and l.price_brl <= l.market_median_brl
)
select
    listing_id,
    car_name, make_name, model_name, body_type, version_key, model_year,
    state, state_name, region, city, source,
    km, market_median_km, km_vs_market,
    transmission, fuel, colour, photos,
    listed_date, days_on_market,
    price_brl, market_p25_brl, market_median_brl, market_p75_brl, comparables,
    gap_to_median_brl, gap_to_median_pct,
    had_price_cut, price_cut_pct,
    target_offer_brl,
    expected_margin_brl,
    margin_at_target_brl,
    case
        when gap_to_median_pct <= -0.08 then 'Buy now'
        when gap_to_median_pct <= -0.03 then 'Negotiate'
        else 'Wait'
    end                                                                     as buy_class,
    case
        when gap_to_median_pct <= -0.08 then 1
        when gap_to_median_pct <= -0.03 then 2
        else 3
    end                                                                     as buy_class_order,
    -- priority inside a class: the deeper the discount, the longer online (a seller more likely to accept an offer)
    -- and the fewer the kilometres against the market, the higher the score
    round(100 * (
        0.6 * least(1, -gap_to_median_pct / 0.15)
      + 0.25 * least(1, days_on_market / 60.0)
      + 0.15 * least(1, greatest(0, -km_vs_market / nullif(market_median_km, 0)))
    ))                                                                      as priority_score
from candidates
