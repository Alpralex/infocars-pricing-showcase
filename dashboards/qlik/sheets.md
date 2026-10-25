# Sheet guide

Four sheets, each answering one question a used-car dealer asks before repricing stock.
Build them in this order with the master items in place. Reference values are for no selections.

## 1. Overview: "Where does the market stand?"
- KPIs: Clean Ads (1,167), Median Asking Price (R$ 78,000), Median Days to Sell (22), Above Market Online (82).
- Filter pane: Model, State Name, Model Year, Body Type.
- Pivot table "What comparable cars are listed for": Car in rows, Model Year in columns,
  Median Asking Price and Clean Ads as measures. **2023 Onix LTZ: 6 ads, median R$ 68,400**, the same as `python scripts/demo.py`.

## 2. Price and speed: "Does an overpriced car take longer to sell?"
- Bar chart: Median Days to Sell by Price Band, excluding `Too few comparables`.
  **17 days below −6%, 20, 20.5, 27.5 and 30 days above +6%.**
- Bar chart: Still Online % by Price Band (8% below −6% against 29% above +6%).
- Scatter: dimension ListingID, x = `Avg([Gap to Median %])`, y = `Avg([Days on Market])`, colour by Price Position,
  with `[Is Sold]={1}` in the measures' set expressions.
- KPI: Sold Within 30 Days % (62.9% overall; select `Below -6%`: 73.9%, `Above +6%`: 51.0%).

## 3. Stock to review: "Which ads still online should be repriced?"
- Straight table: Car, Model Year, State, Price, Market Median, Gap to Median, Gap to Median %, Comparables,
  Days on Market, Price Position, with `Is Active = 1` and Price Position in above market and below market,
  sorted by Gap to Median descending. **82 above market, R$ 530,500 above their medians; 31 below, −R$ 156,950.**
- Bar chart: Gap Above Market Online by Model (Corolla is the largest, R$ 106,900 across 13 ads).
- Line chart: Ads Online on Date by Online Date, with Price Position as the second dimension
  (294 ads online on 2025-10-01, peak 313 on 2025-10-11).

## 4. Data quality: "How many ads can we trust?"
- Bar chart: Ads in Step by Quality Step (1,200 raw, 15 bad price, 0 incomplete, 18 outliers, 1,167 clean).
- Text: 187 clean ads matched through typo correction; 116 make and model spellings reduce to 7 models.
- Table: Match Method with Clean Ads (1,167: 980 exact, 187 fuzzy).

## Bookmarks for the demo video
1. "Overpriced stock": Is Active = 1, Price Position = above market.
2. "Onix in São Paulo": Model = Onix, State = SP (51 ads, median R$ 59,600, 20 days to sell).
3. "Price bands": sheet 2 with no selections.
