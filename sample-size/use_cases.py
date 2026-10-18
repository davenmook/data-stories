"""The numbers behind the "different questions" table in "How many samples are enough?".

simulate.py answers one question: how fast do the median and the 10th
percentile settle? This script asks the follow-ups from the post, using the
same simulated city:

  1. the 90th percentile (the fast end)
  2. the share of tests under 25 Mbps
  3. city A vs city B: which one is faster, by median and by 10th percentile
  4. slicing 1,000 tests by hour of the day
  5. the 12-test screenshot: how often do 3 or more of 12 land under 25 Mbps?

Usage:
    python3 use_cases.py              # 2,000 trials, seed 42
    python3 use_cases.py --seed 7     # different draws, same shape

No external data needed. numpy only (plus simulate.py next to it).
"""
import argparse
from math import comb

import numpy as np

from simulate import FAST_MEDIAN, FAST_SIGMA, SLOW_MEDIAN, SLOW_SIGMA, SLOW_SHARE, draw

SLOW_CUTOFF = 25.0                       # Mbps


def draw_city(rng, size, scale=1.0, slow_median=SLOW_MEDIAN):
    """Like simulate.draw, with knobs for a second city."""
    slow = rng.random(size) < SLOW_SHARE
    fast = rng.lognormal(np.log(FAST_MEDIAN * scale), FAST_SIGMA, size)
    slow_mbps = rng.lognormal(np.log(slow_median * scale), SLOW_SIGMA, size)
    return np.where(slow, slow_mbps, fast)


def typical_err(est, truth):
    return float(np.median(np.abs(est - truth) / truth))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--trials", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    rng, T = np.random.default_rng(args.seed), args.trials

    big = draw(rng, 4_000_000)
    true_med, true_p10, true_p90 = np.percentile(big, [50, 10, 90])
    true_share = float((big < SLOW_CUTOFF).mean())
    print(f"Simulated city: median {true_med:.0f}, p10 {true_p10:.0f}, p90 {true_p90:.0f} Mbps, "
          f"{true_share:.1%} of tests under {SLOW_CUTOFF:.0f} Mbps\n")

    print("1. The fast end: typical miss of the 90th percentile")
    for n in [50, 100, 200, 300]:
        p90 = np.percentile(draw(rng, (T, n)), 90, axis=1)
        print(f"   {n:>5} tests: {typical_err(p90, true_p90):.1%}")

    print(f"\n2. Share under {SLOW_CUTOFF:.0f} Mbps (true {true_share:.1%}): middle 90% of trials")
    for n in [100, 300, 1000, 2000]:
        share = (draw(rng, (T, n)) < SLOW_CUTOFF).mean(axis=1)
        lo, hi = np.percentile(share, [5, 95])
        print(f"   {n:>5} tests: {lo:.1%} to {hi:.1%}")

    print("\n3. City A vs city B: how often the slower city is called slower")
    b_big = draw_city(rng, 4_000_000, scale=0.9)
    print(f"   a) city B has every speed 10% lower (median {np.median(b_big):.0f} vs {true_med:.0f})")
    for n in [100, 300, 1000]:
        a, b = np.median(draw(rng, (T, n)), axis=1), np.median(draw_city(rng, (T, n), scale=0.9), axis=1)
        print(f"      {n:>5} tests each, by median: {(b < a).mean():.0%}")
    c_big = draw_city(rng, 4_000_000, slow_median=SLOW_MEDIAN * 0.8)
    print(f"   b) city C has a slow tail 20% slower (p10 {np.percentile(c_big, 10):.0f} vs {true_p10:.0f})")
    for n in [300, 1000, 2000]:
        a = np.percentile(draw(rng, (T, n)), 10, axis=1)
        c = np.percentile(draw_city(rng, (T, n), slow_median=SLOW_MEDIAN * 0.8), 10, axis=1)
        print(f"      {n:>5} tests each, by 10th percentile: {(c < a).mean():.0%}")

    n = round(1000 / 24)
    s = draw(rng, (T, n))
    print(f"\n4. 1,000 tests sliced by hour: ~{n} per hour. Typical miss per hour: "
          f"median {typical_err(np.median(s, axis=1), true_med):.0%}, "
          f"10th percentile {typical_err(np.percentile(s, 10, axis=1), true_p10):.0%}")
    print(f"   by day of week and hour: ~{1000 / 168:.0f} tests per slice")

    p = true_share
    tail = sum(comb(12, k) * p**k * (1 - p)**(12 - k) for k in range(3, 13))
    print(f"\n5. 3 or more of 12 tests under {SLOW_CUTOFF:.0f} Mbps: {tail:.1%} (about 1 in {1 / tail:.0f})")


if __name__ == "__main__":
    main()
