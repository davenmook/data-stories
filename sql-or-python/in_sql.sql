-- Median download speed by Texas county and quarter, in DuckDB SQL.
-- Two medians:
--   median_tile_mbps      the middle tile (every tile counts once)
--   weighted_median_mbps  the middle *test* (busy tiles count more)
WITH tiles AS (
    SELECT quarter, county_fips, county, quadkey,
           avg_d_kbps / 1000.0 AS d_mbps,
           tests
    FROM read_parquet('../data/tx_tiles_by_county.parquet')
),
ranked AS (
    SELECT *,
           -- running total of tests, slowest tile first
           SUM(tests) OVER (PARTITION BY quarter, county_fips
                            ORDER BY d_mbps, quadkey
                            ROWS UNBOUNDED PRECEDING) AS running_tests,
           SUM(tests) OVER (PARTITION BY quarter, county_fips) AS total_tests
    FROM tiles
)
SELECT quarter, county_fips, county,
       COUNT(*)                         AS tiles,
       SUM(tests)                       AS tests,
       MEDIAN(d_mbps)                   AS median_tile_mbps,
       -- first tile where the running total passes half of all tests
       MIN(d_mbps) FILTER (WHERE running_tests >= total_tests / 2.0)
                                        AS weighted_median_mbps
FROM ranked
GROUP BY ALL
ORDER BY quarter, county_fips;
