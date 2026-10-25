# Master items

Create these under **Master items** after the first reload. Counts use `ListingCounter` (1 per ad)
rather than `Count(ListingID)`, because `ListingID` is a key shared with the days-online table.
Each measure mirrors the DAX measure of the same name in `../powerbi/`.

## Measures

| Name | Expression | Format |
|---|---|---|
| Clean Ads | `Sum(ListingCounter)` | `#,##0` |
| Sold Ads | `Sum({<[Is Sold]={1}>} ListingCounter)` | `#,##0` |
| Ads Still Online | `Sum({<[Is Active]={1}>} ListingCounter)` | `#,##0` |
| Still Online % | `Sum({<[Is Active]={1}>} ListingCounter) / Sum(ListingCounter)` | `0.0%` |
| Ads Online on Date | `Sum({<%Date=, Year=, Month=, YearMonth=, [Week Start]=, Weekday=>} OnlineFlag)` with `Online Date` as the dimension | `#,##0` |
| Ads Sold on Date | `Sum({<[Is Sold]={1}>} ListingCounter)` with `Removed Date` or `Removed Month` as the dimension | `#,##0` |
| Median Asking Price | `Median(Price)` | Money, `R$ #,##0` |
| Average Asking Price | `Avg(Price)` | Money |
| Median Gap to Market % | `Median([Gap to Median %])` | `+0.0%;-0.0%` |
| Ads With Market | `Sum({<[Price Position]-={'too few comparables'}>} ListingCounter)` | `#,##0` |
| Above Market Ads | `Sum({<[Price Position]={'above market'}>} ListingCounter)` | `#,##0` |
| Below Market Ads | `Sum({<[Price Position]={'below market'}>} ListingCounter)` | `#,##0` |
| Above Market % | `Sum({<[Price Position]={'above market'}>} ListingCounter) / Sum({<[Price Position]-={'too few comparables'}>} ListingCounter)` | `0.0%` |
| Median Days to Sell | `Median({<[Is Sold]={1}>} [Days on Market])` | `0.0` |
| Average Days to Sell | `Avg({<[Is Sold]={1}>} [Days on Market])` | `0.0` |
| Sold Within 30 Days % | `Sum({<[Is Sold]={1}, [Days on Market]={"<=30"}>} ListingCounter) / Sum({<[Is Sold]={1}>} ListingCounter)` | `0.0%` |
| Above Market Online | `Sum({<[Is Active]={1}, [Price Position]={'above market'}>} ListingCounter)` | `#,##0` |
| Below Market Online | `Sum({<[Is Active]={1}, [Price Position]={'below market'}>} ListingCounter)` | `#,##0` |
| Gap Above Market Online | `Sum({<[Is Active]={1}, [Price Position]={'above market'}>} [Gap to Median])` | Money |
| Gap Below Market Online | `Sum({<[Is Active]={1}, [Price Position]={'below market'}>} [Gap to Median])` | Money |
| Ads in Step | `Sum([Quality Ads])` | `#,##0` |

`Ads Online on Date` clears selections on the listed-date calendar on purpose: an ad listed in May is
still online in June. Selections on model, state or price position still apply.

## Dimensions

- **Car** (drill-down): Make → Model → Car
- **Geography** (drill-down): Region → State Name
- **Time** (drill-down): Year → YearMonth → %Date (listed date)
- Price Band (sorted by its numeric value), Price Position, Model Year, Body Type, Source, Online Date, Removed Month

## Colours

Assign master colours to `Price Position` so every sheet uses the same ones: below market blue,
within market range grey, above market orange, too few comparables light grey.
