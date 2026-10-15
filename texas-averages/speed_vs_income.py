"""Averages lie: Texas edition, part 2. Do richer counties get faster internet?

Puts each county's median fixed download (Q4 2025) next to its median household income
from the Census ACS. It's a picture of counties, not people: a county's median income and
its median speed test can line up without any one household's income driving its speed.
Rural counties tend to be both lower income and slower to get fiber, so geography does a
lot of the work here. Correlation, not cause.

Input:  ../data/tx_county_mean_median_q4_2025.csv   (run texas_averages.py first)
        ../data/tx_county_income_acs2024.csv         (run fetch_census.py first)
Output: ../data/tx_county_speed_income.csv
        charts/speed-vs-income.{svg,png}
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
sys.path.insert(0, str(HERE.parent / "tools"))
import style  # noqa: E402

ACS_YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
LABEL = ["Harris", "Dallas", "Travis", "Bexar", "Fort Bend", "Collin", "Waller", "Hidalgo", "El Paso"]

speed = pd.read_csv(DATA / "tx_county_mean_median_q4_2025.csv", dtype={"county_fips": str})
income = pd.read_csv(DATA / f"tx_county_income_acs{ACS_YEAR}.csv", dtype={"county_fips": str})
for df in (speed, income):
    df["county_fips"] = df["county_fips"].str.zfill(5)

c = speed.merge(income[["county_fips", "median_hh_income", "moe"]], on="county_fips", how="inner")
missing = len(speed) - len(c)
c.to_csv(DATA / "tx_county_speed_income.csv", index=False)

# Spearman (rank) correlation: does the ordering line up, whatever the shape?
rho = c["median_mbps"].rank().corr(c["median_hh_income"].rank())
print(f"{len(c)} counties with 2,000+ tests and an income estimate ({missing} dropped).")
print(f"Rank correlation, median speed vs median household income: {rho:.2f}")
print("\nFastest and slowest five:")
cols = ["county", "tests", "median_mbps", "median_hh_income"]
print(c.sort_values("median_mbps", ascending=False)[cols].round(0).to_string(index=False, max_rows=10))

style.use()
fig, ax = plt.subplots(figsize=(8.6, 5.6))
size = 18 + 260 * np.sqrt(c["tests"] / c["tests"].max())
ax.scatter(c["median_hh_income"], c["median_mbps"], s=size, color=style.TEAL, alpha=0.8,
           edgecolor=style.CARBON, linewidth=0.6, zorder=2)
for _, r in c[c["county"].isin(LABEL)].iterrows():
    ax.annotate(r["county"], (r["median_hh_income"], r["median_mbps"]), xytext=(8, -4),
                textcoords="offset points", fontsize=9, color=style.FG2)
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v / 1000:.0f}k"))
ax.set_xlabel(f"Median household income (Census ACS 5-year, {ACS_YEAR})")
ax.set_ylabel("Median download, Mbps (Q4 2025)")
ax.set_title("Texas counties: median income vs median fixed download speed")
ax.text(0.98, 0.04, f"Rank correlation {rho:.2f}. Counties, not households,\nso this shows a pattern, not a cause.",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=9, color=style.SAGE)
style.credit(fig, text=style.OOKLA_CREDIT + " (fixed tiles).\nIncome: US Census Bureau ACS 5-year, table B19013."
             " Counties with 2,000+ tests; dot size = number of tests.")
style.save(fig, HERE / "charts" / "speed-vs-income")
