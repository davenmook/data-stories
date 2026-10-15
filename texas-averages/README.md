# Averages lie: Texas edition

**Post:** publishes Dec 2, 2026 on [davenoel.me](https://davenoel.me) (link added when it's live). Follows [Averages lie](https://davenoel.me/notes/averages-lie.html).

Mean vs median fixed download speed for every Texas county with 2,000+ speed tests in Q4 2025.

![Where the average flatters Texas counties](charts/mean-vs-median.png)

## What turned up

- **Statewide, the average actually undersells Texas a little:** mean 392 Mbps, median 401 Mbps.
- **County by county, it's the other way around.** In 58 of 89 counties the average beats the median, and the biggest gaps are all smaller, more rural counties: Palo Pinto (+100 Mbps), Austin (+87), Reeves (+75), Hill (+68) and Fannin (+64). A few fast connections pull the average up while the typical test stays slow.
- **The big metros sit almost on the line.** Lots of tests, lots of fast connections, and the two numbers agree.
- Reeves comes with an asterisk: one very busy tile dominates its tests (see [`sql-or-python/`](../sql-or-python/)).

## Run it

```
pip install -r ../requirements.txt
python3 ../tools/fetch_ookla.py 2025 && mv texas_fixed_2025.parquet ../data/
cd ../sql-or-python && python3 prep.py      # tile centroid -> Texas county (shared step)
cd ../texas-averages && python3 texas_averages.py
```

Writes `../data/tx_county_mean_median_q4_2025.csv` and the chart in `charts/`.

## What these numbers are

- **Mean** is exact: each tile's average speed times its test count, summed, divided by all tests.
- **Median** is the middle test, approximated from tile averages (test-weighted; same method as [`percentiles/`](../percentiles/)).

## Sources

- Speedtest® by Ookla® Global Fixed and Mobile Network Performance Maps, fixed tiles, Q4 2025. Based on analysis by Ookla of Speedtest Intelligence® data. [registry.opendata.aws/speedtest-global-performance](https://registry.opendata.aws/speedtest-global-performance). CC BY-NC-SA 4.0. Ookla trademarks used under license and reprinted with permission.
- County boundaries: US Census Bureau 2010 cartographic boundary file (500k), via [plotly/datasets](https://github.com/plotly/datasets).
