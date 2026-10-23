-- Data quality checks run after every collection.
-- Each query returns one row: the check, how many rows fail it, and the share of the total.
-- Under 0.1% is fine, 0.1% to 1% gets a look, over 1% stops the refresh of the market views.

WITH totals AS (SELECT COUNT(*)::numeric AS n FROM raw_listings)
SELECT check_name, failing, ROUND(100 * failing / NULLIF(totals.n, 0), 2) AS pct
FROM totals, (
    SELECT 'raw ads not matched to the catalogue' AS check_name,
           COUNT(*) AS failing
    FROM raw_listings r
    LEFT JOIN listings l USING (listing_id)
    WHERE l.listing_id IS NULL

    UNION ALL
    SELECT 'duplicate titles from one source on the same day',
           COUNT(*) - COUNT(DISTINCT (source, lower(title), first_seen))
    FROM raw_listings

    UNION ALL
    -- A price far from its peers usually lost or gained a digit when it was typed.
    SELECT 'prices outside 0.5x-2x of their version median',
           COUNT(*)
    FROM listings l
    JOIN mv_market_by_version m
      ON m.model_year = l.model_year
     AND m.state IS NOT DISTINCT FROM l.state
     AND (m.make, m.model, m.version) = (
            SELECT mk.name, md.name, v.name
            FROM versions v JOIN models md USING (model_id) JOIN makes mk USING (make_id)
            WHERE v.version_id = l.version_id)
    WHERE m.listings >= 3
      AND l.price_brl NOT BETWEEN 0.5 * m.median_price_brl AND 2 * m.median_price_brl

    UNION ALL
    SELECT 'mileage above 40,000 km per year of age',
           COUNT(*)
    FROM listings
    WHERE km > 40000 * GREATEST(EXTRACT(year FROM current_date) - model_year, 1)
) checks
ORDER BY pct DESC;
