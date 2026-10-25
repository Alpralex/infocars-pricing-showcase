# InfoCars pricing in Power BI

The same model as the web dashboard, as a Power BI project (PBIP). The semantic model is written in TMDL, so every table, relationship and DAX measure is readable in Git.

## Open it

1. Copy the repository to the Windows machine (in Parallels, for example `C:\infocars-pricing-showcase`).
2. Open `powerbi/InfoCarsPricing.pbip` in Power BI Desktop. If Desktop asks, turn on the PBIP preview in *Options > Preview features*.
3. In *Transform data > Manage parameters*, set **DataFolder** to the folder that holds the Parquet files, with a trailing backslash, for example `C:\infocars-pricing-showcase\dashboards\powerbi\data\`.
4. Select **Refresh**. The model loads about 1,900 rows; the largest table is `fct_listings` with 1,167 ads.

If Desktop refuses the report scaffold, open a blank report instead, go to **TMDL view**, paste the whole of `tmdl-view-script.tmdl` and select **Apply**. That creates the same tables, parameter, relationships and measures.

## Model

Star schema around one row per clean ad:

```
dim_date ────┬── fct_listings            (1,167 clean ads, market comparison per ad)
  (listed_date active, removed_date inactive)
dim_version ─┼── mart_market_by_version  (672 rows: version × model year × state, the production view)
dim_state ───┘
mart_data_quality                        (8 rows, stand-alone: raw ads to clean ads)
```

- `dim_date` is a daily calendar from 1 May to 1 November 2025, marked as the date table (`dataCategory: Time`, key `date_day`).
- `fct_listings[removed_date]` has an inactive relationship to the calendar; **Ads Sold on Date** turns it on with `USERELATIONSHIP`.
- `price_band` sorts by `price_band_order`, `car_name` by the catalogue order, `month_name` by `month_number`.
- No measure shares a name with a column (Power BI names are case-insensitive), so the count is **Clean Ads**, not *Listings*: `mart_market_by_version` has a `listings` column.

| Measure | Definition |
| --- | --- |
| Clean Ads, Sold Ads, Ads Still Online, Still Online % | Row counts over fct_listings; an ad that disappeared counts as sold |
| Ads Online on Date | Ads listed on or before the date and not yet removed on it (ignores the date filter on the fact) |
| Ads Sold on Date | Sold ads by `removed_date`, through the inactive relationship |
| Median Asking Price, Average Asking Price | Over `price_brl` |
| Median Gap to Market % | Median of asking price ÷ median of comparable ads − 1 |
| Above Market Ads, Below Market Ads, Ads With Market, Above Market % | Position against the 25th–75th percentile of comparable ads; ads with fewer than 5 comparables have no position |
| Median Days to Sell, Average Days to Sell, Sold Within 30 Days % | Sold ads only |
| Above Market Online, Below Market Online, Gap Above Market Online, Gap Below Market Online | Ads still online on 1 Nov 2025, and the sum of their gaps to the comparable median |
| Ads in Step | Sum over mart_data_quality |

## Reference numbers (no filters)

| Measure | Value |
| --- | --- |
| Clean Ads / Sold Ads / Ads Still Online | 1,167 / 946 / 221 |
| Median Asking Price / Average Asking Price | R$ 78,000 / R$ 84,635 |
| Median Days to Sell / Average Days to Sell | 22.0 / 30.6 |
| Sold Within 30 Days % | 62.9% |
| Above Market Ads / Below Market Ads / Above Market % | 289 / 292 / 30.6% |
| Above Market Online / Gap Above Market Online | 82 / R$ 530,500 |
| Below Market Online / Gap Below Market Online | 31 / −R$ 156,950 |
| Ads Online on Date, 1 Oct 2025 | 294 (peak 313 on 11 Oct 2025) |
| Ads Sold on Date, September 2025 | 191 |
| Median Days to Sell by `price_band`, Below −6% → Above +6% | 17, 20, 20.5, 27.5, 30 |
| Model = Onix, State = SP | 51 ads, median R$ 59,600, 20 days to sell |

## Report to build (one page, 1280 × 720)

1. **Header:** text box with the question *Which used cars are priced out of line, and how much longer do they take to sell?*
2. **Slicers** in one row: `dim_version[model_name]` (buttons) and `dim_state[state]` (dropdown).
3. **Four cards:** Clean Ads, Median Asking Price, Median Days to Sell (Sold Within 30 Days % as subtitle), Above Market Online (Gap Above Market Online as subtitle).
4. **Column chart:** `fct_listings[price_band]` on the axis, Median Days to Sell as the value, Still Online % in the tooltip. Filter out *Too few comparables*.
5. **Scatter chart:** `fct_listings[listing_id]` as values, `gap_to_median_pct` on x, `days_on_market` on y, `price_position` as legend, filtered to `is_sold = 1` and position not *too few comparables*.
6. **Line chart:** `dim_date[date_day]` on the axis, Ads Online on Date as the value, `fct_listings[price_position]` as the legend (the measure only removes the date filter, so the legend still splits it).
7. **Matrix:** `dim_version[car_name]` in rows, `fct_listings[model_year]` in columns, Median Asking Price and Clean Ads as values.
8. **Table "Stock to review":** car_name, model_year, state, price_brl, market_median_brl, gap_to_median_brl, gap_to_median_pct, days_on_market, price_position, filtered to `is_active = 1` and position above or below market, sorted by gap.
9. **Bar chart:** `mart_data_quality[step]` with Ads in Step.

Publish with *Publish to web* from your own Fabric workspace and put the link in the portfolio.
