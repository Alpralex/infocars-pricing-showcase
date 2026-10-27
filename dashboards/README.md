# InfoCars dashboards: one model in dbt, the web, Power BI and Qlik Sense

The dashboard layer of the InfoCars pricing showcase. It takes the repository's 1,200 synthetic ads, matches them with
the repository's own matcher, rebuilds the quality checks and market statistics in SQL with dbt on DuckDB, and feeds
the same star schema to a web dashboard, a Power BI model and a Qlik Sense app.

The question the dashboards answer is the one InfoCars answered for dealers: **which used cars are priced out of line,
and how much longer do they take to sell?**

**Web:** [`web/`](web/) · **Power BI:** [`powerbi/`](powerbi/) · **Qlik Sense:** [`qlik/`](qlik/)
**Stack:** Python, SQL, dbt, DuckDB, Power BI (PBIP/TMDL, DAX), Qlik Sense (load script, set analysis)

## About the data

The ads are synthetic (`../data/sample_listings.csv`, written by `../scripts/generate_sample_data.py` with a fixed seed).
The generator makes cars priced below market leave the site faster, so finding 1 below checks that the pipeline
recovers a pattern that was put there on purpose. None of the numbers on this page are results of the real business.

The real results are those stated in the main README: about 250,000 listings in the database, 5,114 model spellings
reduced to 641 real models (26,071 ads corrected), a saving of about R$ 2,000 per negotiation at the dealer comparing
the dealer's figures before and after adoption, and time in stock down to 1–3 months. The sample has no dealer
transactions, so the saving per negotiation cannot be recomputed here; the dashboards show the inputs a dealer used
to price: the market for each car, where an ad sits against it, and how that relates to time on the site.

## Findings (snapshot 1 November 2025)

1. **Cars priced under the market sell in about half the time.** Ads more than 6% below the median of comparable ads
   sold in a median of 17 days, and 73.9% of them within 30 days. Ads more than 6% above took 30 days, and 51.0% sold
   within 30 days; 29% of them are still online against 8%.
2. **82 ads still online are priced above the market**, R$ 530,500 above their comparable medians in total
   (a median of +7.8% each), online for a median of 50.5 days.
3. **31 ads still online are priced below the market**, R$ 156,950 under their comparable medians (median −6.1%).
4. **33 of 1,200 ads never reach the statistics:** 15 with no price or one out of range, 18 far from comparable cars.
   187 clean ads were matched only through typo correction, and 116 make and model spellings reduce to 7 models.

## Model

```
../data/sample_listings.csv ─▶ stg_raw_listings ──┐
seeds/listing_matches.csv ───▶ stg_listing_matches ┴─▶ stg_listings_screened   every raw ad + quality outcome
seeds/catalog_versions.csv, seeds/states.csv                     │
                                                                 ▼
             dim_date ─────┐                               fct_listings        1,167 clean ads, market per ad
             dim_version ──┼─────────────────────────────── (version_key, state, listed_date, removed_date)
             dim_state ────┘                                     │
                                                                 ├─▶ mart_market_by_version   port of mv_market_by_version
                                                                 ├─▶ mart_price_position      days to sell by price band
                                                                 ├─▶ mart_stock_out_of_line   ads online outside p25–p75
             stg_listings_screened ───────────────────────────────── mart_data_quality        raw ads to clean ads
```

- **11 models, 56 tests, 3 seeds.** Besides unique, not-null, relationships and accepted values, the tests check that
  every raw ad ends in exactly one outcome, that percentiles are ordered, that each ad's position agrees with its
  percentiles, that days on the market agree with the dates, and that the SQL reproduces the Python demo exactly
  (1,200 raw, 15 bad prices, 18 outliers, 1,167 clean, 187 fuzzy, 116 spellings to 7 models, and a 2023 Onix LTZ
  market of 6 ads with a median of R$ 68,400). `unique_combination` is a generic test for composite keys.
- **Matching** stays in Python: `scripts/match_titles.py` runs `infocars/normalize.py` over the raw titles and writes
  `seeds/listing_matches.csv` and the catalogue (`seeds/catalog_versions.csv`). Everything after matching is SQL.
- **Quality checks** follow `infocars/db.py` in the same order: price missing or outside R$ 5,000–1,500,000, no full
  match, then a price outside 0.5×–2× of the median for the same model, version and year (groups of 3 or more).
- **Market per ad:** the other clean ads of the same version and model year in all states (as `market_price()` without
  a state), so an ad is never its own comparable. Percentiles use `percentile_cont`, as the production view.
  With fewer than 5 comparables there is no market and no position, as the assistant calls such estimates weak.
- **Position** follows `price_position()`: above the 75th percentile is above market, below the 25th is below.
  The price band is the gap to the comparable median: below −6%, −6% to −2%, −2% to +2%, +2% to +6%, above +6%.
- **Days on the market:** an ad that disappears counts as sold on its last day online; ads still online are measured
  to the snapshot. Days to sell use sold ads only, which understates the gap between bands rather than inflating it.
- `mart_market_by_version` is the production materialised view (`../sql/postgres/02_market_views.sql`) in DuckDB,
  with `current_date` replaced by the snapshot date.

## Run it

From this folder, with the repository one level up:

```bash
pip install dbt-duckdb==1.9.1
python scripts/match_titles.py      # optional: rewrites seeds/ from the raw titles (already committed)
dbt build --profiles-dir .          # 11 models, 56 tests, 3 seeds
python scripts/export.py            # powerbi/data/*.parquet and web/data/*.json
cd web && python -m http.server     # then open http://localhost:8000
```

`INFOCARS_DB_PATH` (default `infocars.duckdb` in this folder) and `INFOCARS_RAW_PATH` (default `../data`) override the paths.

## The three tools

| | Web | Power BI | Qlik Sense |
|---|---|---|---|
| Reads | `web/data/listings.json`, `meta.json` | `powerbi/data/*.parquet` | `powerbi/data/*.parquet` |
| Model | the ad rows, aggregated in the browser | star schema in TMDL, 21 DAX measures | one fact, two dimensions, master calendar, days-online table |
| Open | any static server | `powerbi/InfoCarsPricing.pbip`, set DataFolder | load `qlik/load_script.qvs`, set vPath |
| Guide | the page itself | [`powerbi/README.md`](powerbi/README.md) | [`qlik/master_items.md`](qlik/master_items.md), [`qlik/sheets.md`](qlik/sheets.md) |

## Reference numbers

Verified with DuckDB against the marts. With no filters, both apps should show:

| Measure | Value |
| --- | --- |
| Clean ads / sold / still online | 1,167 / 946 / 221 |
| Median / average asking price | R$ 78,000 / R$ 84,635 |
| Median / average days to sell (sold ads) | 22.0 / 30.6 |
| Sold within 30 days | 62.9% |
| Above / within / below market / too few comparables | 289 / 364 / 292 / 222 |
| Above market % (of ads with a market) | 30.6% |
| Above market and online: ads / gap to medians | 82 / R$ 530,500 |
| Below market and online: ads / gap to medians | 31 / −R$ 156,950 |
| Ads online on 1 Oct 2025 (peak) | 294 (313 on 11 Oct 2025) |
| Ads that left the site in September 2025 | 191 |
| Median days to sell by band, below −6% → above +6% | 17 / 20 / 20.5 / 27.5 / 30 |
| Onix in SP: ads / median price / median days to sell | 51 / R$ 59,600 / 20 |
| 2023 Onix LTZ, all states: ads / median price | 6 / R$ 68,400 |
| Data quality: raw / bad price / incomplete / outlier / clean | 1,200 / 15 / 0 / 18 / 1,167 |

## Files

```
dbt_project.yml, profiles.yml   dbt on DuckDB, paths from environment variables
seeds/                          title matches, catalogue, states
models/staging, models/marts    dbt models
tests/generic, tests/singular   unique_combination and the reconciliation tests
scripts/match_titles.py         runs the repository's matcher and writes the seeds
scripts/export.py               Parquet for Power BI and Qlik, JSON for the web page
web/                            static dashboard
powerbi/                        PBIP project: TMDL model, DAX measures, report spec
qlik/                           load script, master items, sheets
```
