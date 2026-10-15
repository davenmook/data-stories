"""How many speed tests is enough? A sample-size simulator.

Companion to the post "How many speed tests is enough? Sample size" (davenoel.me).

The idea: pretend we know the true speed distribution of a made-up town, then
draw n tests from it, again and again, and see how far the measured median and
10th percentile wander from the truth. Small n, lots of wobble. Big n, the
wobble settles down. The interesting part is how much faster the median settles
than the 10th percentile does.

Why made-up? Ookla's open data gives each ~600 m tile the AVERAGE of its tests
plus a count, not the individual tests, so we can't resample real tests from it.
A simulated town lets us know the right answer and measure the error exactly.

The town: most homes on a fast connection, plus a slow tail (old DSL, a busy
evening, a far corner of the house). Both parts are lognormal, which is the usual
shape for speed data: bunched up at the low end, long tail to the right.

Usage:
    python3 simulate.py                 # default sizes, 2,000 trials each
    python3 simulate.py --trials 5000   # smoother bands, a bit slower
    python3 simulate.py --seed 7        # different random draws, same answer shape

Output: results.csv (one row per n) and a plain-text table in the terminal.
The chart comes next, in chart.py.

No external data needed. numpy + pandas only.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent

# The made-up town. Medians in Mbps; sigma is the lognormal spread.
FAST_MEDIAN, FAST_SIGMA = 250.0, 0.45
SLOW_MEDIAN, SLOW_SIGMA = 25.0, 0.70
SLOW_SHARE = 0.15                      # 15% of tests come from the slow tail

SIZES = [10, 20, 30, 50, 75, 100, 200, 300, 500, 1000, 2000, 5000]


def draw(rng, size):
    """Draw speed tests from the made-up town. `size` can be an int or a shape."""
    slow = rng.random(size) < SLOW_SHARE
    fast_mbps = rng.lognormal(np.log(FAST_MEDIAN), FAST_SIGMA, size)
    slow_mbps = rng.lognormal(np.log(SLOW_MEDIAN), SLOW_SIGMA, size)
    return np.where(slow, slow_mbps, fast_mbps)


def true_values(rng, n=4_000_000):
    """The town's 'real' median and p10, from one enormous sample."""
    big = draw(rng, n)
    return float(np.median(big)), float(np.percentile(big, 10))


def wobble(estimates, truth):
    """How far the estimates stray: the middle 90% band, and typical % error."""
    lo, hi = np.percentile(estimates, [5, 95])
    typical_err = float(np.median(np.abs(estimates - truth) / truth))
    return lo, hi, typical_err


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--trials", type=int, default=2000, help="repeat draws per sample size")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    true_med, true_p10 = true_values(rng)
    print(f"Made-up town, true median {true_med:.0f} Mbps, true p10 {true_p10:.0f} Mbps")
    print(f"{args.trials:,} trials per sample size\n")

    rows = []
    for n in SIZES:
        samples = draw(rng, (args.trials, n))           # trials x n tests
        meds = np.median(samples, axis=1)
        p10s = np.percentile(samples, 10, axis=1)
        m_lo, m_hi, m_err = wobble(meds, true_med)
        p_lo, p_hi, p_err = wobble(p10s, true_p10)
        rows.append({
            "n": n,
            "median_lo": m_lo, "median_hi": m_hi, "median_typical_err": m_err,
            "p10_lo": p_lo, "p10_hi": p_hi, "p10_typical_err": p_err,
        })

    df = pd.DataFrame(rows)
    df.insert(1, "true_median", true_med)
    df.insert(2, "true_p10", true_p10)
    df.round(4).to_csv(HERE / "results.csv", index=False)

    print(f"{'n':>6}  {'median, 90% of trials':>24}  {'typ err':>7}  "
          f"{'p10, 90% of trials':>20}  {'typ err':>7}")
    for r in rows:
        print(f"{r['n']:>6}  {r['median_lo']:>10.0f} to {r['median_hi']:<10.0f}  "
              f"{r['median_typical_err']:>6.1%}  {r['p10_lo']:>8.0f} to {r['p10_hi']:<8.0f}  "
              f"{r['p10_typical_err']:>6.1%}")
    print(f"\nsaved {HERE / 'results.csv'}")


if __name__ == "__main__":
    main()
