# Which samples are you looking at?

**Post:** [Which samples are you looking at?](https://davenoel.me/notes/which-samples.html), Oct 23, 2026

The same simulated city as [`sample-size/`](../sample-size/), but now tests come from households, and households don't all test the same amount. 5% of homes are power users who run 40 tests a month on a faster plan. Everyone else runs zero to three.

## Run it

```bash
python3 sampling.py            # builds the town, prints the table, then checks 2,000 towns
python3 sampling.py --seed 7   # different draws, same shape
```

Change `POWER_SHARE`, `POWER_TESTS` or `POWER_SPEEDUP` at the top to see how far the every-test median drifts. numpy only, no downloads.

## The plain-English answer

Counting every test, the town looks 54% faster than it really is, because 5% of homes ran 59% of the tests. Giving each home one vote brings the median back within a few percent of the truth. You trade 3,483 tests for 767 homes, and 767 is the honest sample size.
