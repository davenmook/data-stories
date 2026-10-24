# Five SQL patterns I use every week

**Post:** [Five SQL patterns I use every week](https://davenoel.me/notes/five-sql-patterns.html), Oct 23, 2026

Five patterns, each with a tiny example on Ookla open data, **fixed tiles**, Texas, 2025, in DuckDB SQL.

| # | Pattern | What the example asks |
| --- | --- | --- |
| 1 | `read_parquet` in place | Tiles and tests per quarter, straight off the file |
| 2 | `GROUP BY ALL` | Median tile download by quarter for Harris, Travis and Loving counties |
| 3 | `FILTER` | Counties with the biggest share of tests in tiles averaging under 100 Mbps (Q4) |
| 4 | Running totals with a window | How many counties hold half of all fixed tests (Q4) |
| 5 | CTEs that stack steps | Biggest Q1 to Q4 change in test-weighted mean download |

## Run it

From `data-stories/`, with the venv active:

```bash
python3 tools/fetch_ookla.py 2025          # then move the file into data/
python3 sql-or-python/prep.py              # tiles to counties -> data/tx_tiles_by_county.parquet
python3 sql-patterns/run.py                # runs each block in patterns.sql and prints it
```

Or paste any one block from `patterns.sql` into the DuckDB CLI from inside `sql-patterns/`.

## Caveats

- Fixed tiles only. Tiles carry average speeds and test counts, so "per test" numbers are test-weighted averages of tile averages, and pattern 3 counts tests in tiles whose *average* is under 100 Mbps.
- These count tests, not homes. A home that tests a lot counts a lot.
- Pattern 5's top county (Milam) shows why to check a jump: its mean went from 149 to 295 Mbps while its median tile went from 89 to 96.

## Sources

- Speedtest® by Ookla® Global Fixed and Mobile Network Performance Maps, fixed tiles, 2025. Based on analysis by Ookla of Speedtest Intelligence® data. CC BY-NC-SA 4.0. https://registry.opendata.aws/speedtest-global-performance
- County boundaries: US Census Bureau cartographic boundary file, via plotly/datasets.
