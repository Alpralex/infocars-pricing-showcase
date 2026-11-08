# InfoCars pricing in Power BI

**Live report (Publish to web):** https://app.powerbi.com/view?r=eyJrIjoiMTYxODFjYTUtYjZmOC00NDQ5LTgxZmQtNDA5Y2I5YmMzMDdlIiwidCI6IjY2MDMwOWU1LWI1YWEtNDQzNS1iMDU2LTJhYmViOGZmNDZjNyJ9

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

## Report pages and what to try

The report has three pages, a navigation bar on every page and the Almanac theme. Every magenta sentence is a DAX measure that rewrites itself with the filters.

1. **Start here.** The question, the live answer for each page (select it to open the page), how to use the report and how it is built.
2. **Market.** Which ads are priced above their market range and how much longer they take to sell: four cards, median days to sell by price band, gap to market against days to sell, ads online by day, median price by car and model year, and the data-quality funnel. Headline with no filters: *Of 1,167 clean ads, 289 (31% of those with enough comparables) were priced above their market range. They took a median of 35 days to sell, against 20 for ads within range and 18 for ads below it. 82 overpriced ads are still online.*
3. **Price review.** A what-if **Price cut** parameter (0% to 15%, default 5%) applied to the overpriced ads still online. Cards, a bar chart by car and the ad-level table show how many ads the cut brings back into their market range (at or below the 75th percentile of comparable ads) and how much asking price it gives up. Headline at 5%: *A 5% price cut would bring 63 of the 82 overpriced ads still online back into their market range, for R$ 371,365 less in asking price.* At 3% it is 41 ads, at 10% 80.

The model and slicer filters are synced between Market and Price review. Auto date/time is off, so the model has no hidden date tables; `dim_date` is the only calendar. Every base measure has a description, visible when you hover over it in the Data pane.

| What-if measure | Definition |
| --- | --- |
| Price Cut Value | The chosen cut, from the `Price Cut` table (GENERATESERIES 0–15) |
| Back in Range After Cut, Back in Range After Cut % | Overpriced ads still online whose price × (1 − cut) ≤ `market_p75_brl` |
| Asking Price Given Up | Sum of price × cut over the overpriced ads still online |
| Price After Cut | Price × (1 − cut) for one ad |
| Median Days to Sell Above Market, Median Days to Sell In Range | Median Days to Sell for sold ads in each price position |

`tmdl-view-script.tmdl` still creates the original one-page model, without the what-if table and the headline measures.

Publish with *Publish to web* from your own Fabric workspace and put the link in the portfolio.
