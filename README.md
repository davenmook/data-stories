# Data Stories

The lab behind [Overthinking the Internet](https://davenoel.me). Every post that leans on data gets a folder here, so you can rerun the numbers yourself and check my work. (Please do. I overthink, but I'm not infallible!)

Public data only. Every chart and every folder credits its sources.

## Post ↔ folder map

| Post | Publishes | Folder | Status |
| --- | --- | --- | --- |
| [SQL or Python? Yes.](https://davenoel.me/notes/sql-or-python.html) | Oct 13, 2026 | [`sql-or-python/`](sql-or-python/) | Live |
| [Percentiles: the 10th tells you who's suffering](https://davenoel.me/notes/percentiles.html) | Oct 14, 2026 | [`percentiles/`](percentiles/) | Live |
| [The data that isn't there: Hurricane Beryl](https://davenoel.me/stories/the-data-that-isnt-there.html) | Oct 15, 2026 | [`beryl/`](beryl/) | Live |
| [Averages lie: Texas edition](https://davenoel.me/notes/averages-lie.html) (an update to the Averages lie note) | Oct 16, 2026 | [`texas-averages/`](texas-averages/) | Live |
| [How many samples are enough?](https://davenoel.me/notes/how-many-samples.html) | Oct 19, 2026 | [`sample-size/`](sample-size/) | Live |
| [Which samples are you looking at?](https://davenoel.me/notes/which-samples.html) | Oct 23, 2026 | [`sampling/`](sampling/) | Live |
| [Five SQL patterns I use every week](https://davenoel.me/notes/five-sql-patterns.html) | Oct 23, 2026 | [`sql-patterns/`](sql-patterns/) | Live |
| How steady is a household's internet? Variance | Oct 29, 2026 | [`variance/`](variance/) | Coming soon |
| Normalization: per test, per person, per household | Nov 2, 2026 | [`normalization/`](normalization/) | Coming soon |

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
