# SQL or Python? Yes.

**Post:** [davenoel.me/notes/sql-or-python.html](https://davenoel.me/notes/sql-or-python.html)

One question, answered twice: what's the median fixed download speed in each Texas county, each quarter of 2025? Once in DuckDB SQL, once in pandas, with a check that both land on the same numbers.

Two medians, because they answer different questions:

- `median_tile_mbps`: the middle tile. Every ~600 m tile counts once.
- `weighted_median_mbps`: the middle *test*. Tiles with more tests count more.

## Run it

```
pip install -r ../requirements.txt
python3 ../tools/fetch_ookla.py 2025       # writes texas_fixed_2025.parquet; move it into ../data/
cd sql-or-python
python3 prep.py                            # tile centroid -> Texas county
python3 compare.py                         # runs in_sql.sql and in_pandas.py, asserts they match
```

| File | What it does |
| --- | --- |
| `prep.py` | Shared step: point-in-polygon join of tile centroids to Texas counties |
| `in_sql.sql` | Both medians in DuckDB SQL (window functions) |
| `in_pandas.py` | Both medians in pandas (groupby + cumsum) |
| `compare.py` | Runs both, fails loudly if they disagree, writes `../data/tx_county_medians_2025.csv` |

## Sources

- Speedtest® by Ookla® Global Fixed and Mobile Network Performance Maps, fixed tiles, 2025 Q1–Q4. Based on analysis by Ookla of Speedtest Intelligence® data. [registry.opendata.aws/speedtest-global-performance](https://registry.opendata.aws/speedtest-global-performance). CC BY-NC-SA 4.0. Ookla trademarks used under license and reprinted with permission.
- County boundaries: US Census Bureau 2010 cartographic boundary file (500k), via [plotly/datasets](https://github.com/plotly/datasets).

Data is reaggregated by Ookla from time to time, so a rerun on a later date can shift numbers slightly.
