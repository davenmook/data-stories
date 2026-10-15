"""Averages lie: Texas edition. Mean vs median download speed for every Texas county.

Companion to "Averages lie" (https://davenoel.me/notes/averages-lie.html).

For each county with 2,000+ speed tests in Q4 2025:
  mean    the average speed across all tests (exact: each tile's average x its test count)
  median  the middle test (test-weighted median of tile averages; see the percentiles README)

A positive gap (mean above median) means the average makes the county look faster than
a typical test. A negative gap means the average undersells it.

Input:  ../data/tx_tiles_by_county.parquet   (run ../sql-or-python/prep.py first)
Output: ../data/tx_county_mean_median_q4_2025.csv
        charts/mean-vs-median.{svg,png}
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
sys.path.insert(0, str(HERE.parent / "tools"))
import style  # noqa: E402

QUARTER = 4
MIN_TESTS = 2000
LABEL_TOP = 5


def weighted_median(mbps, tests):
    order = np.argsort(mbps, kind="stable")
    mbps, tests = mbps[order], tests[order]
    running = np.cumsum(tests)
    return float(mbps[np.searchsorted(running, 0.5 * running[-1])])


def summarize(df):
    m, t = df["d_mbps"].to_numpy(), df["tests"].to_numpy()
    return pd.Series({"tiles": len(df), "tests": int(t.sum()),
                      "mean_mbps": float((m * t).sum() / t.sum()),
                      "median_mbps": weighted_median(m, t)})


tiles = pd.read_parquet(DATA / "tx_tiles_by_county.parquet")
tiles["d_mbps"] = tiles["avg_d_kbps"] / 1000.0
q = tiles[tiles["quarter"] == QUARTER]

texas = summarize(q)
print(f"Texas, Q{QUARTER} 2025: mean {texas['mean_mbps']:.0f} Mbps, median {texas['median_mbps']:.0f} Mbps")

c = q.groupby(["county_fips", "county"]).apply(summarize, include_groups=False).reset_index()
c = c[c["tests"] >= MIN_TESTS].copy()
c[["tiles", "tests"]] = c[["tiles", "tests"]].astype(int)
c["gap_mbps"] = c["mean_mbps"] - c["median_mbps"]
c["gap_pct"] = 100 * c["gap_mbps"] / c["median_mbps"]
c = c.sort_values("gap_mbps", ascending=False)
c.round(1).to_csv(DATA / f"tx_county_mean_median_q{QUARTER}_2025.csv", index=False)

above = (c["gap_mbps"] > 0).sum()
print(f"{len(c)} counties with {MIN_TESTS:,}+ tests; the average beats the median in {above} of them.")
print("\nBiggest gaps (average makes the county look faster):")
print(c.head(LABEL_TOP)[["county", "tests", "mean_mbps", "median_mbps", "gap_mbps"]].round(0).to_string(index=False))
print("\nAverage undersells the county the most:")
print(c.tail(3)[["county", "tests", "mean_mbps", "median_mbps", "gap_mbps"]].round(0).to_string(index=False))

# Chart: median (x) vs mean (y). Above the line = the average flatters the county.
style.use()
fig, ax = plt.subplots(figsize=(8, 6.4))
lim = (0, max(c["mean_mbps"].max(), c["median_mbps"].max()) * 1.08)
ax.plot(lim, lim, color=style.MUTED, linewidth=1, linestyle="--", zorder=1)
ax.text(lim[1] * 0.16, lim[1] * 0.12, "mean = median", color=style.MUTED, fontsize=9, ha="center", rotation=45,
        rotation_mode="anchor")
size = 18 + 260 * np.sqrt(c["tests"] / c["tests"].max())
colors = np.where(c["gap_mbps"] > 0, style.SAGE, style.NEUTRAL)
ax.scatter(c["median_mbps"], c["mean_mbps"], s=size, color=colors, alpha=0.85, edgecolor=style.CARBON,
           linewidth=0.6, zorder=2)
for _, r in c.head(LABEL_TOP).iterrows():
    # nudge labels apart when two counties sit close together
    near = c.head(LABEL_TOP)[(abs(c.head(LABEL_TOP)["median_mbps"] - r["median_mbps"]) < 25)
                             & (abs(c.head(LABEL_TOP)["mean_mbps"] - r["mean_mbps"]) < 25)]
    up = len(near) > 1 and r["mean_mbps"] >= near["mean_mbps"].max()
    down = len(near) > 1 and not up
    ax.annotate(f"{r['county']} +{r['gap_mbps']:.0f}", (r["median_mbps"], r["mean_mbps"]),
                xytext=(-10, 10) if up else ((10, -14) if down else (10, -4)), textcoords="offset points",
                ha="right" if up else "left", fontsize=9, color=style.FG2)
ax.set_xlim(lim)
ax.set_ylim(lim)
ax.set_aspect("equal")
ax.set_xlabel("Median download, Mbps (the middle test)")
ax.set_ylabel("Mean download, Mbps (the average)")
ax.set_title(f"Where the average flatters Texas counties (fixed broadband, Q{QUARTER} 2025)")
ax.text(0.02, 0.98, f"Above the line: the average looks faster\nthan a typical test ({above} of {len(c)} counties)",
        transform=ax.transAxes, va="top", fontsize=9, color=style.SAGE)
ax.text(0.98, 0.04, "Below: the average undersells it", transform=ax.transAxes, ha="right", fontsize=9,
        color=style.MUTED)
style.credit(fig, text=style.OOKLA_CREDIT + f" (fixed tiles).\nTexas counties with {MIN_TESTS:,}+ tests; dot size = number of tests.")
style.save(fig, HERE / "charts" / "mean-vs-median")
