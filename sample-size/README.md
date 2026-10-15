# How many speed tests is enough? Sample size

**Post:** publishes Oct 21, 2026 on [davenoel.me](https://davenoel.me) (link added when it's live)

A little simulator: draw n tests and watch the median and p10 wobble as n grows.

## Run it

```bash
python3 simulate.py            # writes results.csv, prints a table
```

`simulate.py` invents a town with a known speed distribution (mostly fast, with a slow tail), draws n tests from it 2,000 times per n, and measures how far the median and 10th percentile wander from the truth. No downloads needed.

First look: the median settles fast (about 5% typical error by 100 tests), but the 10th percentile is a lot jumpier and needs roughly ten times as many tests to settle down as much. Chart and the plain-English answer coming next.

Why simulated? Ookla's open data gives tile averages and test counts, not individual tests, so there's nothing real to resample. A made-up town means we know the right answer and can measure the miss exactly.
