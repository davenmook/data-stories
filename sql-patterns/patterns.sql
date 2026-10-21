-- Five SQL patterns I use every week, in DuckDB SQL.
-- Data: Ookla open data, FIXED tiles, Texas, 2025 (tiles carry average speeds
-- and test counts, so anything "per test" below is a test-weighted tile average).
-- Run from sql-patterns/:  python3 run.py   (or paste one block into duckdb)
-- Needs ../data/texas_fixed_2025.parquet (tools/fetch_ookla.py 2025) and
-- ../data/tx_tiles_by_county.parquet (sql-or-python/prep.py).

-- name: 1. Query the file where it sits
-- No import step. DuckDB reads the parquet file like a table.
SELECT quarter,
       COUNT(*)   AS tiles,
       SUM(tests) AS tests
FROM read_parquet('../data/texas_fixed_2025.parquet')
GROUP BY quarter
ORDER BY quarter;

-- name: 2. GROUP BY ALL
-- Group by every column that isn't an aggregate, so the list never drifts.
SELECT county, quarter,
       COUNT(*)                           AS tiles,
       SUM(tests)                         AS tests,
       ROUND(MEDIAN(avg_d_kbps) / 1000)   AS median_tile_mbps
FROM read_parquet('../data/tx_tiles_by_county.parquet')
WHERE county IN ('Harris', 'Travis', 'Loving')
GROUP BY ALL
ORDER BY county, quarter;

-- name: 3. FILTER for conditional counts
-- Several "how many of them..." columns in one pass, no CASE WHEN.
SELECT county,
       SUM(tests)                                          AS tests,
       SUM(tests) FILTER (WHERE avg_d_kbps < 100000)       AS tests_under_100,
       ROUND(100.0 * SUM(tests) FILTER (WHERE avg_d_kbps < 100000)
             / SUM(tests), 1)                              AS pct_under_100
FROM read_parquet('../data/tx_tiles_by_county.parquet')
WHERE quarter = 4
GROUP BY ALL
HAVING SUM(tests) >= 5000
ORDER BY pct_under_100 DESC
LIMIT 5;

-- name: 4. Running totals with a window
-- How many counties hold half of all Texas tests? Sort, then keep a running sum.
WITH by_county AS (
    SELECT county, SUM(tests) AS tests
    FROM read_parquet('../data/tx_tiles_by_county.parquet')
    WHERE quarter = 4
    GROUP BY ALL
)
SELECT county, tests,
       ROW_NUMBER() OVER (ORDER BY tests DESC)                      AS rank,
       ROUND(100.0 * SUM(tests) OVER (ORDER BY tests DESC
                                      ROWS UNBOUNDED PRECEDING)
             / SUM(tests) OVER (), 1)                               AS running_pct
FROM by_county
ORDER BY tests DESC
LIMIT 8;

-- name: 5. CTEs that stack small steps
-- Each step has a name, so you can read it top to bottom and test each one.
WITH tiles AS (               -- step 1: just the columns we need, in Mbps
    SELECT county, quarter, tests, avg_d_kbps / 1000.0 AS d_mbps
    FROM read_parquet('../data/tx_tiles_by_county.parquet')
),
county_q AS (                 -- step 2: test-weighted mean per county and quarter
    SELECT county, quarter, SUM(tests) AS tests,
           SUM(d_mbps * tests) / SUM(tests) AS mean_mbps
    FROM tiles
    GROUP BY ALL
),
change AS (                   -- step 3: Q1 to Q4, counties with enough tests
    SELECT county,
           MAX(mean_mbps) FILTER (WHERE quarter = 1) AS q1_mbps,
           MAX(mean_mbps) FILTER (WHERE quarter = 4) AS q4_mbps,
           MIN(tests) AS min_tests
    FROM county_q
    GROUP BY ALL
)
SELECT county,
       ROUND(q1_mbps) AS q1_mbps,
       ROUND(q4_mbps) AS q4_mbps,
       ROUND(100 * (q4_mbps / q1_mbps - 1), 1) AS pct_change
FROM change
WHERE min_tests >= 1000
ORDER BY pct_change DESC
LIMIT 5;
