"""Download Texas fixed-broadband tiles from Ookla open data.

Pulls all four quarters of one year straight from Ookla's public S3 bucket
(no AWS account needed), keeps only tiles inside a Texas bounding box, and
writes one small Parquet file. DuckDB only downloads the columns and row
groups it needs, so this takes a few minutes, not a full global download.

Usage:
    pip install duckdb
    python3 fetch_ookla.py            # 2025, writes texas_fixed_2025.parquet
    python3 fetch_ookla.py 2024       # any year from 2023 on (tile_x/tile_y exist from Q3 2023)
    python3 fetch_ookla.py 2024 mobile  # mobile (cellular) tiles instead of fixed, writes texas_mobile_2024.parquet

Data: Speedtest by Ookla Global Fixed and Mobile Network Performance Maps,
CC BY-NC-SA 4.0. https://registry.opendata.aws/speedtest-global-performance
"""
import sys
import time

import duckdb

YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2025
KIND = sys.argv[2] if len(sys.argv) > 2 else "fixed"
if KIND not in ("fixed", "mobile"):
    raise SystemExit("Second argument must be 'fixed' or 'mobile'.")

# Generous Texas bounding box (lon/lat). Counties get assigned later with a
# proper point-in-polygon join, so a few Oklahoma/Louisiana/Mexico tiles near
# the edges are fine here.
XMIN, XMAX, YMIN, YMAX = -106.65, -93.50, 25.83, 36.50

BASE = f"https://ookla-open-data.s3.amazonaws.com/parquet/performance/type={KIND}"
urls = [
    f"{BASE}/year={YEAR}/quarter={q}/{YEAR}-{(q - 1) * 3 + 1:02d}-01_performance_{KIND}_tiles.parquet"
    for q in range(1, 5)
]
out = f"texas_{KIND}_{YEAR}.parquet"

con = duckdb.connect()
con.sql("INSTALL httpfs; LOAD httpfs;")

start = time.time()
file_list = ", ".join(f"'{u}'" for u in urls)
con.sql(f"""
    COPY (
        SELECT
            CAST(regexp_extract(filename, 'quarter=([1-4])', 1) AS INTEGER) AS quarter,
            quadkey, tile_x, tile_y,
            avg_d_kbps, avg_u_kbps, avg_lat_ms, tests, devices
        FROM read_parquet([{file_list}], filename = true)
        WHERE tile_x BETWEEN {XMIN} AND {XMAX}
          AND tile_y BETWEEN {YMIN} AND {YMAX}
    ) TO '{out}' (FORMAT parquet, COMPRESSION zstd)
""")

print(f"Wrote {out} in {time.time() - start:.0f}s")
print(con.sql(f"""
    SELECT quarter, count(*) AS tiles, sum(tests) AS tests
    FROM '{out}' GROUP BY quarter ORDER BY quarter
"""))
