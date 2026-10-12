# Data Stories

The lab behind [Overthinking the Internet](https://davenoel.me). Every post that leans on data gets a folder here, so you can rerun the numbers yourself and check my work. (Please do. I overthink, but I'm not infallible!)

Public data only. Every chart and every folder credits its sources.

## Post ↔ folder map

| Post | Publishes | Folder | Status |
| --- | --- | --- | --- |
| Percentiles: the 10th tells you who's suffering | Oct 14, 2026 | [`percentiles/`](percentiles/) | Coming soon |
| How many speed tests is enough? Sample size | Oct 21, 2026 | [`sample-size/`](sample-size/) | Coming soon |
| SQL or Python? Yes. | Oct 28, 2026 | [`sql-or-python/`](sql-or-python/) | Coming soon |
| The data that isn't there: Hurricane Beryl | Nov 4, 2026 | [`beryl/`](beryl/) | Coming soon |
| Same average, different internet: variance | Nov 11, 2026 | [`variance/`](variance/) | Coming soon |
| Comparing cities fairly: normalization | Nov 18, 2026 | [`normalization/`](normalization/) | Coming soon |
| Five SQL patterns I use every week | Nov 25, 2026 | [`sql-patterns/`](sql-patterns/) | Coming soon |
| Averages lie: Texas edition | Dec 2, 2026 | [`texas-averages/`](texas-averages/) | Coming soon |

Shared helpers (data download scripts, chart style) live in [`tools/`](tools/).

## Run it yourself

```bash
git clone https://github.com/davenmook/data-stories.git
cd data-stories
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Each folder's README says what to run. Raw data is downloaded by script into `data/` and never committed, so the repo stays small and every source keeps its own license.

## Data sources and credit

- **Ookla open data** (speed test performance tiles): [Speedtest® by Ookla® Global Fixed and Mobile Network Performance Maps](https://github.com/teamookla/ookla-open-data), licensed [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). Anything here built on it is shared under the same terms.
- More sources (NOAA, IODA, FCC DIRS, US Census) get credited in the folders that use them as they land.

## License

Code is [MIT](LICENSE). Data belongs to its sources and follows their licenses (see above).

Views are my own.
