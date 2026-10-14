"""Percentiles on real Texas speed test data.

Companion to the post "Percentiles: the 10th tells you who's suffering"
(https://davenoel.me/notes/percentiles.html).

Three things:
  1. Texas-wide 10th, 50th and 90th percentile download speed, each quarter of 2025.
  2. Counties whose medians are about the same but whose 10th percentiles are far apart
     (the real-data version of the post's made-up Town A and Town B).
  3. Two charts in the site's style.

A note on what these numbers are: Ookla's open data comes as ~600 m tiles, and each
tile carries the AVERAGE of the tests inside it plus a test count. We don't get the
individual tests. So "the 10th percentile" here means: line the tiles up slowest to
fastest, count tests as you go, and stop where you pass 10% of all tests. That's a
test-weighted percentile of tile averages, which is close to, but not the same as, the
10th percentile of individual tests. Tile averages smooth out the extremes, so the
real 10th percentile of tests is likely lower than what you see here.

Input:  ../data/tx_tiles_by_county.parquet   (run ../sql-or-python/prep.py first)
Output: ../data/tx_percentiles_2025.csv
        ../data/tx_county_percentiles_q4_2025.csv
        charts/texas-distribution.{svg,png}
        charts/same-median-different-p10.{svg,png}
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

QUARTER = 4            # quarter used for the county comparison and charts
MIN_TESTS = 2000       # skip counties with too few tests to say much
MEDIAN_WINDOW = 0.05   # "same median" = within 5% of each other


def weighted_quantile(mbps, tests, q):
    """Speed at which the running test count first reaches q of all tests (slowest first)."""
    order = np.argsort(mbps, kind="stable")
    mbps, tests = np.asarray(mbps)[order], np.asarray(tests)[order]
    running = np.cumsum(tests)
    return float(mbps[np.searchsorted(running, q * running[-1])])


def summarize(df):
    m, t = df["d_mbps"].to_numpy(), df["tests"].to_numpy()
    return pd.Series({
        "tiles": len(df),
        "tests": t.sum(),
        "p10_mbps": weighted_quantile(m, t, 0.10),
        "median_mbps": weighted_quantile(m, t, 0.50),
        "p90_mbps": weighted_quantile(m, t, 0.90),
    })


tiles = pd.read_parquet(DATA / "tx_tiles_by_county.parquet")
tiles["d_mbps"] = tiles["avg_d_kbps"] / 1000.0

# 1. Texas-wide, by quarter
texas = tiles.groupby("quarter").apply(summarize, include_groups=False).reset_index()
texas[["tiles", "tests"]] = texas[["tiles", "tests"]].astype(int)
texas["gap_x"] = texas["median_mbps"] / texas["p10_mbps"]
texas.round(1).to_csv(DATA / "tx_percentiles_2025.csv", index=False)
print("Texas fixed download, test-weighted percentiles of tile averages (Mbps):")
print(texas.round(1).to_string(index=False))

# 2. Counties: same median, different 10th percentile
q = tiles[tiles["quarter"] == QUARTER]
counties = (q.groupby(["county_fips", "county"]).apply(summarize, include_groups=False)
              .reset_index())
counties[["tiles", "tests"]] = counties[["tiles", "tests"]].astype(int)
counties = counties[counties["tests"] >= MIN_TESTS].copy()
counties.round(1).to_csv(DATA / f"tx_county_percentiles_q{QUARTER}_2025.csv", index=False)

best = None
c = counties.sort_values("median_mbps").reset_index(drop=True)
for i, a in c.iterrows():
    near = c[(c.index > i) & (c["median_mbps"] <= a["median_mbps"] * (1 + MEDIAN_WINDOW))]
    for _, b in near.iterrows():
        gap = abs(a["p10_mbps"] - b["p10_mbps"])
        if best is None or gap > best[0]:
            best = (gap, a, b)

if best is None:
    sys.exit(f"No two counties have medians within {MEDIAN_WINDOW:.0%}; raise MEDIAN_WINDOW.")
_, a, b = best
pair = pd.DataFrame([a, b]).sort_values("p10_mbps", ascending=False)
print(f"\nQ{QUARTER} 2025, counties with {MIN_TESTS:,}+ tests and medians within "
      f"{MEDIAN_WINDOW:.0%} of each other, biggest 10th-percentile gap:")
print(pair[["county", "tests", "p10_mbps", "median_mbps", "p90_mbps"]].round(1).to_string(index=False))

# 3. Charts
style.use()
q4 = texas[texas["quarter"] == QUARTER].iloc[0]

# 3a. Where Texas tests land, with the 10th percentile and median marked
fig, ax = plt.subplots(figsize=(9, 4.6))
cap = q["d_mbps"].quantile(0.99)
bins = np.linspace(0, cap, 60)
ax.hist(q["d_mbps"].clip(upper=cap), bins=bins, weights=q["tests"],
        color=style.NEUTRAL, edgecolor=style.CARBON, linewidth=0.4)
ax.hist(q["d_mbps"][q["d_mbps"] <= q4["p10_mbps"]], bins=bins,
        weights=q["tests"][q["d_mbps"] <= q4["p10_mbps"]],
        color=style.TEAL, edgecolor=style.CARBON, linewidth=0.4)
for x, label, color in ((q4["p10_mbps"], "10th percentile", style.TEAL),
                        (q4["median_mbps"], "median", style.FG)):
    ax.axvline(x, color=color, linewidth=1.5, linestyle="--")
    ax.text(x, ax.get_ylim()[1] * 0.97, f" {label}\n {x:,.0f} Mbps", color=color,
            va="top", fontsize=10)
ax.set_title(f"Texas fixed broadband, Q{QUARTER} 2025: the slowest 10% of tests in teal")
ax.set_xlabel(f"Tile average download speed (Mbps, tiles above {cap:,.0f} grouped in the last bar)")
ax.set_ylabel("Speed tests")
ax.yaxis.set_major_formatter(lambda v, _: f"{v / 1000:,.0f}k" if v >= 1000 else f"{v:,.0f}")
ax.grid(axis="x", visible=False)
style.credit(fig)
style.save(fig, HERE / "charts" / "texas-distribution")

# 3b. Same median, different 10th percentile
fig, ax = plt.subplots(figsize=(9, 3.2))
for y, (_, r) in enumerate(pair.iterrows()):
    ax.plot([r["p10_mbps"], r["p90_mbps"]], [y, y], color=style.GRID, linewidth=8,
            solid_capstyle="round", zorder=1)
    ax.scatter(r["p10_mbps"], y, s=110, color=style.TEAL, zorder=3)
    ax.scatter(r["median_mbps"], y, s=110, color=style.FG, zorder=3)
    ax.scatter(r["p90_mbps"], y, s=60, color=style.SAGE, zorder=3)
    ax.text(r["p10_mbps"], y + 0.22, f"p10 {r['p10_mbps']:,.0f}", color=style.TEAL,
            ha="center", fontsize=9.5)
    ax.text(r["median_mbps"], y - 0.32, f"median {r['median_mbps']:,.0f}", color=style.FG,
            ha="center", fontsize=9.5)
ax.set_yticks(range(len(pair)), [f"{n} County" for n in pair["county"]])
ax.set_ylim(-0.7, len(pair) - 0.3)
ax.set_xlim(left=0)
ax.set_xlabel("Download speed (Mbps): 10th percentile, median and 90th percentile")
ax.set_title(f"Same median, very different bottom 10% (Q{QUARTER} 2025)")
ax.grid(axis="y", visible=False)
style.credit(fig)
style.save(fig, HERE / "charts" / "same-median-different-p10")
