// Generates the PBIR pages, visuals and "InfoCarsPricing" theme for dashboards/powerbi/InfoCarsPricing.Report.
// Run from the repo root: node scripts/build_powerbi_report.mjs
// The script owns every page listed below and the InfoCarsPricing theme; it rewrites them on each run.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const REPORT = path.resolve("dashboards/powerbi/InfoCarsPricing.Report");
const DEF = path.join(REPORT, "definition");
const VISUAL_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json";
const PAGE_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json";

// Same visual style as the AtlanticaFPA report in finance-fpa-analytics.
const C = {
  page: "#F7F8F9", card: "#FFFFFF", border: "#DCE0E5", text: "#1B2430", muted: "#5D6876", grid: "#ECEFF2",
  blue: "#2A78D6", orange: "#EB6834", green: "#1F7A35", amber: "#B25B00", grey: "#5D6876", red: "#B42318",
  greenSoft: "#E3F1E6", redSoft: "#FBE4E1", subtotal: "#EEF1F4",
};

// ---------- expression helpers ----------
const lit = (v) => ({ expr: { Literal: { Value: v } } });
const str = (s) => lit(`'${s.replace(/'/g, "''")}'`);
const num = (n) => lit(`${n}D`);
const int = (n) => lit(`${n}L`);
const bool = (b) => lit(b ? "true" : "false");
const fill = (hex) => ({ solid: { color: lit(`'${hex}'`) } });
const col = (entity, prop) => ({ Column: { Expression: { SourceRef: { Entity: entity } }, Property: prop } });
const proj = (field) => {
  const f = field.Column || field.Measure;
  const entity = f.Expression.SourceRef.Entity;
  return { field, queryRef: `${entity}.${f.Property}`, nativeQueryRef: f.Property };
};
const named = (field, displayName) => ({ ...proj(field), displayName });
const ref = (field) => proj(field).queryRef;
const id = (...parts) => crypto.createHash("sha1").update(parts.join("|")).digest("hex").slice(0, 20);
const filterId = (...parts) => "Filter" + crypto.createHash("sha1").update(parts.join("|")).digest("hex").slice(0, 24);

// Basic visual-level filter: column IN (literals).
function inFilter(page, key, field, literals) {
  const c = field.Column;
  const entity = c.Expression.SourceRef.Entity;
  return {
    name: filterId(page, key),
    field,
    type: "Categorical",
    filter: {
      Version: 2,
      From: [{ Name: "f", Entity: entity, Type: 0 }],
      Where: [{
        Condition: {
          In: {
            Expressions: [{ Column: { Expression: { SourceRef: { Source: "f" } }, Property: c.Property } }],
            Values: literals.map((v) => [{ Literal: { Value: v } }]),
          },
        },
      }],
    },
    howCreated: "User",
  };
}

// Column NOT IN (literals).
function notInFilter(page, key, field, literals) {
  const f = inFilter(page, key, field, literals);
  f.filter.Where[0].Condition = { Not: { Expression: f.filter.Where[0].Condition } };
  return f;
}


// ---------- fields ----------
const MEASURE_TABLE = { "Ads in Step": "mart_data_quality" };
const meas = (prop) => ({ Measure: { Expression: { SourceRef: { Entity: MEASURE_TABLE[prop] || "fct_listings" } }, Property: prop } });
const fl = (name) => col("fct_listings", name);
// Sum of a listing column: with one ad per scatter point it is the ad value itself.
const sumOf = (name, displayName) => ({
  field: { Aggregation: { Expression: fl(name), Function: 0 } },
  queryRef: `Sum(fct_listings.${name})`,
  nativeQueryRef: `Sum of ${name}`,
  displayName,
});

const F = {
  model: col("dim_version", "model_name"),
  car: col("dim_version", "car_name"),
  state: col("dim_state", "state"),
  day: col("dim_date", "date_day"),
  position: fl("price_position"),
  band: fl("price_band"),
  step: col("mart_data_quality", "step"),
};

// Above market in orange, below in blue, within range in grey.
const POSITION_COLOR = { "above market": C.orange, "below market": C.blue, "within market range": "#AEB6BF" };
const positionScope = (value) => ({
  data: [{ scopeId: { Comparison: { ComparisonKind: 0, Left: F.position, Right: { Literal: { Value: `'${value}'` } } } } }],
});
const positionColors = Object.entries(POSITION_COLOR).map(([v, c]) => ({ properties: { fill: fill(c) }, selector: positionScope(v) }));
const withMarket = (page, key) => notInFilter(page, key, F.position, ["'too few comparables'"]);

function slicers(page) {
  const model = container(page, "slicer_model", { x: 792, y: 16, w: 240, h: 80 }, {
    visualType: "slicer",
    syncGroup: { groupName: "ModelSync", fieldChanges: true, filterChanges: true },
    query: { queryState: { Values: { projections: [proj(F.model)] } } },
    objects: {
      data: [{ properties: { mode: str("Dropdown") } }],
      header: [{ properties: { show: bool(true), text: str("Model") } }],
    },
    visualContainerObjects: {
      general: [{ properties: { altText: str("Car model filter dropdown.") } }],
      padding: [vcoPadding(8)],
    },
  });
  const state = container(page, "slicer_state", { x: 1048, y: 16, w: 216, h: 80 }, {
    visualType: "slicer",
    syncGroup: { groupName: "StateSync", fieldChanges: true, filterChanges: true },
    query: { queryState: { Values: { projections: [proj(F.state)] } } },
    objects: {
      data: [{ properties: { mode: str("Dropdown") } }],
      header: [{ properties: { show: bool(true), text: str("State") } }],
    },
    visualContainerObjects: {
      general: [{ properties: { altText: str("Brazilian state filter dropdown.") } }],
      padding: [vcoPadding(8)],
    },
  });
  return [model, state];
}

// ---------- pages ----------
const PAGE_IDS = { pricing: "b1c2d3e4f5a6b7c8d901" };

function pricingPage() {
  const p = PAGE_IDS.pricing;
  z = 0;
  const cards = [
    card(p, "card_clean_ads", { x: 16, y: 104, w: 300, h: 120 }, meas("Clean Ads"), "Clean ads", {
      units: "1", reference: { field: meas("Ads Still Online"), title: "still online" }, alt: "Number of clean ads, and how many are still online.",
    }),
    card(p, "card_median_price", { x: 332, y: 104, w: 300, h: 120 }, meas("Median Asking Price"), "Median asking price", {
      units: "1000", precision: 1, alt: "Median asking price in Brazilian reais.",
    }),
    card(p, "card_days_to_sell", { x: 648, y: 104, w: 300, h: 120 }, meas("Median Days to Sell"), "Median days to sell", {
      reference: { field: meas("Sold Within 30 Days %"), title: "sold within 30 days" },
      alt: "Median days on the market for sold ads, and the share sold within 30 days.",
    }),
    card(p, "card_above_online", { x: 964, y: 104, w: 300, h: 120 }, meas("Above Market Online"), "Ads above market, still online", {
      units: "1", reference: { field: meas("Gap Above Market Online"), title: "over market median", units: "1000", precision: 1 },
      alt: "Ads still online that are priced above the market range, and how much they ask over the comparable median in total.",
    }),
  ];
  const days = meas("Median Days to Sell");
  const byBand = container(p, "column_days_band", { x: 16, y: 240, w: 400, h: 216 }, {
    visualType: "columnChart",
    query: {
      queryState: {
        Category: { projections: [named(F.band, "Price against market")] },
        Y: { projections: [named(days, "Median days to sell")] },
        Tooltips: { projections: [named(meas("Still Online %"), "Still online")] },
      },
      sortDefinition: { sort: [{ field: F.band, direction: "Ascending" }], isDefaultSort: true },
    },
    objects: {
      dataPoint: [{ properties: { fill: fill(C.blue) } }],
      labels: [{ properties: { show: bool(true), fontSize: num(10), color: fill(C.text) } }],
      categoryAxis: [{ properties: { ...axisOn, fontSize: num(9) } }],
      valueAxis: [{ properties: { show: bool(false), gridlineShow: bool(false), showAxisTitle: bool(false) } }],
      legend: [{ properties: { show: bool(false) } }],
    },
    visualContainerObjects: chartVcos("Median days to sell, by price against market",
      "Column chart of median days to sell for sold ads, from priced more than 6% below the comparable median to more than 6% above; dearer ads take longer.",
      "Sold ads, by gap to the comparable median"),
  }, { filterConfig: { filters: [notInFilter(p, "band_with_market", F.band, ["'Too few comparables'"])] } });
  const scatter = container(p, "scatter_gap_days", { x: 432, y: 240, w: 416, h: 216 }, {
    visualType: "scatterChart",
    query: {
      queryState: {
        Category: { projections: [named(fl("listing_id"), "Ad")] },
        Series: { projections: [named(F.position, "Position")] },
        X: { projections: [sumOf("gap_to_median_pct", "Gap to market median")] },
        Y: { projections: [sumOf("days_on_market", "Days on market")] },
      },
    },
    objects: {
      dataPoint: positionColors,
      bubbles: [{ properties: { bubbleSize: int(-10) } }],
      categoryAxis: [{ properties: { ...axisOn, showAxisTitle: bool(true), gridlineShow: bool(true), gridlineColor: fill(C.grid) } }],
      valueAxis: [{ properties: { ...axisOn, showAxisTitle: bool(true), gridlineShow: bool(true), gridlineColor: fill(C.grid) } }],
      legend: legendTop,
    },
    visualContainerObjects: chartVcos("Gap to market against days to sell",
      "Scatter plot of sold ads: gap to the comparable median on the horizontal axis and days on the market on the vertical axis, coloured by position against the market range.",
      "Sold ads with at least 5 comparables"),
  }, { filterConfig: { filters: [inFilter(p, "scatter_sold", fl("is_sold"), ["1L"]), withMarket(p, "scatter_market")] } });
  const online = container(p, "line_online", { x: 864, y: 240, w: 400, h: 216 }, {
    visualType: "lineChart",
    query: {
      queryState: {
        Category: { projections: [named(F.day, "Date")] },
        Y: { projections: [named(meas("Ads Online on Date"), "Ads online")] },
        Series: { projections: [named(F.position, "Position")] },
      },
    },
    objects: {
      dataPoint: positionColors,
      lineStyles: [{ properties: { strokeWidth: num(2), lineChartType: str("linear"), areaShow: bool(false) } }],
      legend: legendTop,
      labels: [{ properties: { show: bool(false) } }],
      categoryAxis: [{ properties: { ...axisOn } }],
      valueAxis: [{ properties: { ...axisOn, gridlineShow: bool(true), gridlineColor: fill(C.grid) } }],
    },
    visualContainerObjects: chartVcos("Ads online by day",
      "Line chart of the number of ads online each day, one line per position against the market range.", "May to November 2025"),
  }, { filterConfig: { filters: [withMarket(p, "online_market")] } });
  const matrix = container(p, "matrix_price_year", { x: 16, y: 472, w: 376, h: 232 }, {
    visualType: "pivotTable",
    query: {
      queryState: {
        Rows: { projections: [named(F.car, "Car")] },
        Columns: { projections: [named(fl("model_year"), "Model year")] },
        Values: { projections: [named(meas("Median Asking Price"), "Median price"), named(meas("Clean Ads"), "Ads")] },
      },
    },
    objects: {
      columnHeaders: [{ properties: { columnAdjustment: str("growToFit"), autoSizeColumnWidth: bool(true), fontSize: num(9) } }],
      rowHeaders: [{ properties: { fontSize: num(9) } }],
      values: [{ properties: { fontSize: num(9) } }],
      columnFormatting: [{ properties: { labelDisplayUnits: str("1000"), labelPrecision: int(0) }, selector: { metadata: ref(meas("Median Asking Price")) } }],
    },
    visualContainerObjects: chartVcos("Median asking price by car and model year",
      "Matrix of the median asking price and number of ads for each car version by model year.", "R$ thousands"),
  });
  const review = container(p, "table_stock_review", { x: 408, y: 472, w: 592, h: 232 }, {
    visualType: "tableEx",
    query: {
      queryState: {
        Values: {
          projections: [
            named(F.car, "Car"), named(fl("model_year"), "Year"), named(F.state, "State"),
            named(fl("price_brl"), "Price"), named(fl("market_median_brl"), "Market"),
            named(fl("gap_to_median_brl"), "Gap"), named(fl("gap_to_median_pct"), "Gap %"),
            named(fl("days_on_market"), "Days"), named(F.position, "Position"),
          ],
        },
      },
      sortDefinition: { sort: [{ field: fl("gap_to_median_brl"), direction: "Descending" }], isDefaultSort: true },
    },
    objects: {
      columnHeaders: [{ properties: { columnAdjustment: str("growToFit"), autoSizeColumnWidth: bool(true), fontSize: num(9) } }],
      values: [{ properties: { fontSize: num(9) } }],
      total: [{ properties: { totals: bool(false) } }],
    },
    visualContainerObjects: chartVcos("Stock to review",
      "Table of ads still online priced above or below the market range, with car, model year, state, price, market median, gap in reais and percent, days on the market and position, largest gap first.",
      "Still online, outside the market range, largest gap first"),
  }, {
    filterConfig: {
      filters: [
        inFilter(p, "review_active", fl("is_active"), ["1L"]),
        inFilter(p, "review_position", F.position, ["'above market'", "'below market'"]),
      ],
    },
  });
  const quality = container(p, "bar_data_quality", { x: 1016, y: 472, w: 248, h: 232 }, {
    visualType: "clusteredBarChart",
    query: {
      queryState: {
        Category: { projections: [named(F.step, "Step")] },
        Y: { projections: [named(meas("Ads in Step"), "Ads")] },
      },
      sortDefinition: { sort: [{ field: F.step, direction: "Ascending" }], isDefaultSort: true },
    },
    objects: {
      dataPoint: [{ properties: { fill: fill(C.grey) } }],
      labels: [{ properties: { show: bool(true), fontSize: num(9), color: fill(C.text), labelDisplayUnits: num(1) } }],
      categoryAxis: [{ properties: { ...axisOn, fontSize: num(8) } }],
      valueAxis: [{ properties: { show: bool(false), gridlineShow: bool(false), showAxisTitle: bool(false) } }],
      legend: [{ properties: { show: bool(false) } }],
    },
    visualContainerObjects: chartVcos("From raw ads to clean ads",
      "Bar chart of the data cleaning steps: raw ads collected, ads dropped at each check, and clean ads matched to the catalogue.", "Data quality funnel"),
  });
  return {
    name: p, displayName: "Pricing",
    visuals: [...header(p, "Which used cars are priced out of line?", "And how much longer do they take to sell? Used-car ads in Brazil, May to November 2025"),
      ...slicers(p), ...cards, byBand, scatter, online, matrix, review, quality],
  };
}


// ---------- visual builders ----------
let z = 0;
function container(page, key, pos, visual, extra = {}) {
  z += 1000;
  return {
    $schema: VISUAL_SCHEMA,
    name: id(page, key),
    position: { x: pos.x, y: pos.y, z, height: pos.h, width: pos.w, tabOrder: z },
    visual,
    ...extra,
  };
}

const vcoPadding = (p) => ({ properties: { top: num(p), bottom: num(p), left: num(p), right: num(p) } });

function chartVcos(title, alt, subtitle) {
  return {
    title: [{ properties: { show: bool(true), text: str(title) } }],
    general: [{ properties: { altText: str(alt) } }],
    padding: [vcoPadding(12)],
    // Without an explicit subtitle Desktop shows an auto-generated one in the UI language.
    subTitle: [{ properties: subtitle ? { show: bool(true), text: str(subtitle) } : { show: bool(false) } }],
  };
}

function textbox(page, key, pos, text, style) {
  return container(page, key, pos, {
    visualType: "textbox",
    objects: {
      general: [{
        properties: {
          paragraphs: [{ textRuns: [{ value: text, textStyle: style }], horizontalTextAlignment: "left" }],
        },
      }],
    },
    visualContainerObjects: {
      background: [{ properties: { show: bool(false) } }],
      border: [{ properties: { show: bool(false) } }],
      padding: [vcoPadding(0)],
    },
  });
}

function header(page, title, subtitle) {
  return [
    textbox(page, "title", { x: 16, y: 16, w: 600, h: 40 }, title,
      { fontFamily: "Segoe UI Semibold", fontSize: "22px", color: C.text }),
    textbox(page, "subtitle", { x: 16, y: 58, w: 600, h: 40 }, subtitle,
      { fontFamily: "Segoe UI", fontSize: "13px", color: C.muted }),
  ];
}

// Entity (multi-select dropdown) and fiscal year (single select, preset to 2026), synced across pages.
function card(page, key, pos, field, label, opts = {}) {
  const objects = {
    value: [{
      properties: {
        fontSize: num(20),
        ...(opts.units ? { labelDisplayUnits: str(opts.units) } : {}),
        ...(opts.precision !== undefined ? { labelPrecision: int(opts.precision) } : {}),
      },
      selector: { id: "default" },
    }],
    label: [{ properties: { show: bool(true), text: str(label), fontSize: num(11), fontColor: fill(C.muted) }, selector: { id: "default" } }],
    padding: [{ properties: { paddingUniform: num(8) }, selector: { id: "default" } }],
    layout: [{ properties: { paddingUniform: num(0) }, selector: { id: "default" } }],
    outline: [{ properties: { show: bool(false) }, selector: { id: "default" } }],
    divider: [{ properties: { show: bool(false) }, selector: { id: "default" } }],
  };
  if (opts.reference) {
    const refId = id(page, key, "ref");
    const sel = { data: [{ dataViewWildcard: { matchingOption: 0 } }], metadata: ref(field), id: refId, order: 0 };
    const partSel = { data: [{ dataViewWildcard: { matchingOption: 1 } }], metadata: ref(field), id: refId };
    objects.referenceLabel = [{ properties: { value: { expr: opts.reference.field } }, selector: sel }];
    const titleProps = { show: bool(true), titleContentType: str("custom"), titleText: str(opts.reference.title), titleFontColor: fill(C.muted) };
    objects.referenceLabelTitle = [
      { properties: titleProps, selector: { id: "default" } },
      { properties: titleProps, selector: partSel },
    ];
    const valueProps = { show: bool(true), valueFontColor: opts.reference.signColor ? signFont(opts.reference.field) : fill(C.text), valueBold: bool(true) };
    if (opts.reference.units) valueProps.valueDisplayUnits = str(opts.reference.units);
    if (opts.reference.precision !== undefined) valueProps.valuePrecision = int(opts.reference.precision);
    objects.referenceLabelValue = [{ properties: valueProps, selector: partSel }];
  }
  return container(page, key, pos, {
    visualType: "cardVisual",
    query: { queryState: { Data: { projections: [proj(field)] } } },
    objects,
    visualContainerObjects: {
      title: [{ properties: { show: bool(false) } }],
      general: [{ properties: { altText: str(opts.alt || label) } }],
      padding: [vcoPadding(8)],
      spacing: [{ properties: { customizeSpacing: bool(true), verticalSpacing: num(2) }, selector: { id: "default" } }],
    },
  });
}

// Green when the measure is above zero, red when below (the reporting sign makes > 0 favourable on every line).
function signCases(field, pos, neg) {
  return {
    expr: {
      Conditional: {
        Cases: [
          { Condition: { Comparison: { ComparisonKind: 1, Left: field, Right: { Literal: { Value: "0D" } } } }, Value: { Literal: { Value: `'${pos}'` } } },
          { Condition: { Comparison: { ComparisonKind: 3, Left: field, Right: { Literal: { Value: "0D" } } } }, Value: { Literal: { Value: `'${neg}'` } } },
        ],
      },
    },
  };
}
const signFont = (field) => ({ solid: { color: signCases(field, C.green, C.red) } });
const signBack = (field) => ({ solid: { color: signCases(field, C.greenSoft, C.redSoft) } });

const axisOn = { show: bool(true), fontSize: num(10), labelColor: fill(C.muted), showAxisTitle: bool(false) };
const legendTop = [{ properties: { show: bool(true), position: str("Top"), fontSize: num(10), labelColor: fill(C.muted) } }];

function lineChart(page, key, pos, category, series, title, alt, opts = {}) {
  return container(page, key, pos, {
    visualType: "lineChart",
    query: {
      queryState: {
        Category: { projections: [proj(category)] },
        Y: { projections: series.map((s) => named(s.field, s.name)) },
      },
    },
    objects: {
      dataPoint: series.map((s) => ({ properties: { fill: fill(s.color) }, selector: { metadata: ref(s.field) } })),
      lineStyles: [
        { properties: { strokeWidth: num(2), lineChartType: str("linear"), areaShow: bool(false) } },
        ...series.filter((s) => s.dashed).map((s) => ({ properties: { lineStyle: str("dashed") }, selector: { metadata: ref(s.field) } })),
      ],
      legend: legendTop,
      labels: [{ properties: { show: bool(false) } }],
      categoryAxis: [{ properties: { ...axisOn } }],
      valueAxis: [{ properties: { ...axisOn, gridlineShow: bool(true), gridlineColor: fill(C.grid), ...(opts.units ? { labelDisplayUnits: str(opts.units) } : {}) } }],
    },
    visualContainerObjects: chartVcos(title, alt, opts.subtitle),
  }, opts.filters ? { filterConfig: { filters: opts.filters } } : {});
}


// ---------- theme ----------
function theme(name) {
  const axis = { gridlineColor: { solid: { color: C.grid } }, labelColor: { solid: { color: C.muted } } };
  return {
    $schema: "https://raw.githubusercontent.com/microsoft/powerbi-desktop-samples/main/Report%20Theme%20JSON%20Schema/reportThemeSchema-2.153.json",
    name,
    dataColors: [C.blue, C.orange, C.green, C.amber, C.grey],
    good: C.green, neutral: C.grey, bad: C.red,
    maximum: "#256ABF", center: "#79A6DD", minimum: "#CDE2FB", null: C.grey,
    foreground: C.text, foregroundNeutralSecondary: C.muted, foregroundNeutralTertiary: C.muted,
    background: C.card, backgroundLight: C.grid, backgroundNeutral: C.border, tableAccent: C.blue,
    textClasses: {
      callout: { fontSize: 20, fontFace: "Segoe UI Semibold", color: C.text },
      title: { fontSize: 12, fontFace: "Segoe UI Semibold", color: C.text },
      header: { fontSize: 12, fontFace: "Segoe UI Semibold", color: C.text },
      label: { fontSize: 10, fontFace: "Segoe UI", color: C.text },
    },
    visualStyles: {
      "*": {
        "*": {
          background: [{ show: true, color: { solid: { color: C.card } }, transparency: 0 }],
          border: [{ show: true, color: { solid: { color: C.border } }, radius: 6, width: 1 }],
          dropShadow: [{ show: false }],
          padding: [{ top: 8, bottom: 8, left: 8, right: 8 }],
          title: [{ show: true, fontFamily: "Segoe UI Semibold", fontSize: 12, fontColor: { solid: { color: C.text } } }],
          subTitle: [{ fontFamily: "Segoe UI", fontSize: 10, fontColor: { solid: { color: C.muted } } }],
          categoryAxis: [{ ...axis, gridlineStyle: "solid" }],
          valueAxis: [{ ...axis, gridlineStyle: "solid" }],
          legend: [{ labelColor: { solid: { color: C.muted } } }],
        },
      },
      textbox: { "*": { padding: [{ top: 0, bottom: 0, left: 0, right: 0 }], background: [{ show: false }], border: [{ show: false }] } },
      cardVisual: { "*": { value: [{ bold: true, $id: "default" }], label: [{ show: true, $id: "default" }], title: [{ show: false }] } },
      slicer: {
        "*": {
          header: [{ fontFamily: "Segoe UI Semibold", textSize: 10, fontColor: { solid: { color: C.text } }, outlineStyle: 0 }],
          items: [{ fontFamily: "Segoe UI", textSize: 10, fontColor: { solid: { color: C.text } }, outlineStyle: 0, padding: 2 }],
        },
      },
      tableEx: {
        "*": {
          columnHeaders: [{ autoSizeColumnWidth: true, columnAdjustment: "growToFit", backColor: { solid: { color: C.page } }, fontColor: { solid: { color: C.text } }, bold: true }],
          values: [{ backColorPrimary: { solid: { color: C.card } }, backColorSecondary: { solid: { color: "#FAFBFC" } }, fontColorPrimary: { solid: { color: C.text } }, fontColorSecondary: { solid: { color: C.text } } }],
        },
      },
      pivotTable: {
        "*": {
          columnHeaders: [{ autoSizeColumnWidth: true, columnAdjustment: "growToFit", backColor: { solid: { color: C.page } }, fontColor: { solid: { color: C.text } }, bold: true }],
          rowHeaders: [{ fontColor: { solid: { color: C.text } } }],
          values: [{ backColorPrimary: { solid: { color: C.card } }, backColorSecondary: { solid: { color: C.card } }, fontColorPrimary: { solid: { color: C.text } }, fontColorSecondary: { solid: { color: C.text } } }],
        },
      },
    },
  };
}

// ---------- write ----------
const write = (file, obj) => {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(obj, null, 2) + "\n");
};

const pages = [pricingPage()];
for (const page of pages) {
  const dir = path.join(DEF, "pages", page.name);
  fs.rmSync(path.join(dir, "visuals"), { recursive: true, force: true });
  write(path.join(dir, "page.json"), {
    $schema: PAGE_SCHEMA,
    name: page.name,
    displayName: page.displayName,
    displayOption: "FitToPage",
    height: 720,
    width: 1280,
    objects: {
      background: [{ properties: { color: fill(C.page), transparency: num(0) } }],
      outspace: [{ properties: { color: fill(C.page), transparency: num(0) } }],
    },
    ...(page.filters ? { filterConfig: { filters: page.filters } } : {}),
  });
  for (const v of page.visuals) write(path.join(dir, "visuals", v.name, "visual.json"), v);
}

const pagesJsonPath = path.join(DEF, "pages", "pages.json");
const pagesJson = JSON.parse(fs.readFileSync(pagesJsonPath, "utf8"));
pagesJson.pageOrder = pages.map((p) => p.name);
pagesJson.activePageName = pages[0].name;
write(pagesJsonPath, pagesJson);

// Theme: rotate the file name on every run so Desktop does not serve a cached copy.
const regDir = path.join(REPORT, "StaticResources", "RegisteredResources");
fs.mkdirSync(regDir, { recursive: true });
for (const f of fs.readdirSync(regDir)) if (/^InfoCarsPricing-[0-9a-f]+\.json$/.test(f)) fs.rmSync(path.join(regDir, f));
const themeName = `InfoCarsPricing-${crypto.randomBytes(4).toString("hex")}.json`;
write(path.join(regDir, themeName), theme(themeName));

const reportPath = path.join(DEF, "report.json");
const report = JSON.parse(fs.readFileSync(reportPath, "utf8"));
report.themeCollection.customTheme = {
  name: themeName,
  reportVersionAtImport: report.themeCollection.baseTheme.reportVersionAtImport,
  type: "RegisteredResources",
};
report.resourcePackages = report.resourcePackages.filter((r) => r.type !== "RegisteredResources");
report.resourcePackages.push({
  name: "RegisteredResources",
  type: "RegisteredResources",
  items: [{ name: themeName, path: themeName, type: "CustomTheme" }],
});
write(reportPath, report);

console.log(`Wrote ${pages.length} pages, ${pages.reduce((n, p) => n + p.visuals.length, 0)} visuals, theme ${themeName}`);
