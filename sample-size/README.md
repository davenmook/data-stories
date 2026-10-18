# How many samples are enough?

**Post:** publishes Nov 4, 2026 on [davenoel.me](https://davenoel.me) (link added when it's live)

A simulated city with a known speed distribution: 85% of tests from a fast group (median 250 Mbps), 15% from a slow tail (median 25 Mbps). Draw n tests from it, thousands of times, and watch how far the median and the 10th percentile wander from the truth.

## Run it

```bash
python3 simulate.py      # writes results.csv and prints the wobble table
python3 use_cases.py     # the follow-up questions: 90th percentile, share under 25 Mbps, city vs city, slicing by hour
```

Add `--seed 7` to either one for different draws with the same overall shape. No downloads needed, just numpy and pandas.

## The plain-English answer

The median steadies (typical miss under 5%) at ~100 tests. The 10th percentile needs ~2,000 to 3,000 to get as steady, because it lives in the thin part of the distribution where few tests land. The post walks through the math: error shrinks with the square root of n, and the 10th percentile starts out about 5.7 times as uncertain, so it needs about 32 times the tests.
