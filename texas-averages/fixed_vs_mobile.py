"""Averages lie: Texas edition, part 3. Does income line up differently for fixed and mobile?

Same question as speed_vs_income.py, asked twice: once with Ookla's fixed tiles (home
broadband) and once with its mobile tiles (cellular). They're separate datasets with no
provider or technology split, so each panel stands on its own.

Uses the same quarter for both: Q4 2025 by default (python3 fixed_vs_mobile.py 2024 for Q4 2024).
Each panel also shows the middle county (median of the county medians) as a dashed line. Not the
Texas-wide median: in Q4 2025 one mobile tile in Collin County held 29% of all Texas mobile tests,
so a statewide median would mostly be that one tile.

No trend line on purpose: with rank correlations around 0.2 to 0.3, a fitted line would point
the eye at a slope the data barely has. The labelled counties are the ones that stand out.

Watch for one busy tile: if a single tile holds most of a county's tests, that county's median
is really that tile's average. Those counties are drawn hollow and flagged in the CSV.

Median = the middle test, approximated from tile averages (test-weighted, like percentiles/).
Ookla tiles are ~600 m squares holding the average of their tests, so a tile's slow and fast
tests are already blended before we start. Tiles are placed in a county by their centre point.

Input:  ../data/texas_fixed_<YEAR>.parquet, ../data/texas_mobile_<YEAR>.parquet
        ../data/tx_county_income_acs<ACS>.csv   (run fetch_census.py first; newest year used)
Output: ../data/tx_county_fixed_mobile_income_q4_<YEAR>.csv
        charts/fixed-vs-mobile-income.{svg,png}
"""
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter, MultipleLocator

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
sys.path.insert(0, str(HERE.parent / "tools"))
import style  # noqa: E402

YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2025
QUARTER = 4
MIN_TESTS = {"fixed": 2000, "mobile": 500}   # mobile has far fewer tests per county
ONE_TILE = 0.5                                # flag counties where one tile holds over half the tests

# Counties to name in each panel, with label offsets in points, picked for Q4 2025.
LABEL = {
    "fixed": {"Cameron": (-10, 14, "right"), "Hidalgo": (-10, -18, "right"), "Reeves": (10, -4, "left"),
              "Kendall": (10, -4, "left"), "Fort Bend": (-6, 14, "right"), "Harris": (8, -16, "left")},
    "mobile": {"Cameron": (-6, -18, "center"), "Hidalgo": (12, -10, "left"), "Rockwall": (-10, 0, "right"),
               "Wichita": (10, -4, "left"), "Collin": (14, 12, "left"), "Harris": (-10, 8, "right")},
}
COUNTIES_URL = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
ACS = max(int(p.stem[-4:]) for p in DATA.glob("tx_county_income_acs*.csv"))


def weighted_median(mbps, tests):
    order = np.argsort(mbps, kind="stable")
    mbps, tests = mbps[order], tests[order]
    running = np.cumsum(tests)
    return float(mbps[np.searchsorted(running, 0.5 * running[-1])])


path = DATA / "us_counties.geojson"
counties = gpd.read_file(path if path.exists() else COUNTIES_URL)
tx = counties.loc[counties["STATE"] == "48", ["id", "geometry"]].rename(columns={"id": "county_fips"})
tx = tx.to_crs("EPSG:4326")

income = pd.read_csv(DATA / f"tx_county_income_acs{ACS}.csv", dtype={"county_fips": str})
income["county_fips"] = income["county_fips"].str.zfill(5)

parts = []
for kind in ("fixed", "mobile"):
    t = pd.read_parquet(DATA / f"texas_{kind}_{YEAR}.parquet")
    t = t[t["quarter"] == QUARTER]
    pts = gpd.GeoDataFrame(t, geometry=gpd.points_from_xy(t["tile_x"], t["tile_y"]), crs="EPSG:4326")
    j = pd.DataFrame(gpd.sjoin(pts, tx, predicate="within", how="inner").drop(columns="geometry"))
    j["d_mbps"] = j["avg_d_kbps"] / 1000
    c = j.groupby("county_fips").apply(lambda df: pd.Series({
        "tests": int(df["tests"].sum()),
        "median_mbps": weighted_median(df["d_mbps"].to_numpy(), df["tests"].to_numpy()),
        "top_tile_share": df["tests"].max() / df["tests"].sum()}),
        include_groups=False).reset_index()
    c = c[c["tests"] >= MIN_TESTS[kind]]
    c["kind"] = kind
    parts.append(c)

out = pd.concat(parts).merge(income[["county_fips", "county", "median_hh_income"]], on="county_fips")
out["tests"] = out["tests"].astype(int)
out["one_tile"] = out["top_tile_share"] > ONE_TILE
out.round(1).to_csv(DATA / f"tx_county_fixed_mobile_income_q{QUARTER}_{YEAR}.csv", index=False)

rho = {}
for kind, g in out.groupby("kind"):
    rho[kind] = g["median_mbps"].rank().corr(g["median_hh_income"].rank())
    print(f"{kind:>6}: {len(g)} counties with {MIN_TESTS[kind]:,}+ tests, "
          f"rank correlation with income {rho[kind]:.2f}, "
          f"middle county {g['median_mbps'].median():.0f} Mbps")
    for _, r in g[g["one_tile"]].iterrows():
        print(f"        one busy tile: {r['county']} ({r['top_tile_share']:.0%} of {r['tests']:,} tests in one tile)")

style.use()
fig, axes = plt.subplots(1, 2, figsize=(11, 5.8), sharex=True, sharey=True)
for ax, kind, color in zip(axes, ("fixed", "mobile"), (style.SAGE, style.TEAL)):
    g = out[out["kind"] == kind]
    size = 14 + 200 * np.sqrt(g["tests"] / g["tests"].max())
    solid, hollow = g[~g["one_tile"]], g[g["one_tile"]]
    ax.scatter(solid["median_hh_income"], solid["median_mbps"], s=size[~g["one_tile"]], color=color, alpha=0.8,
               edgecolor=style.CARBON, linewidth=0.6, zorder=2)
    ax.scatter(hollow["median_hh_income"], hollow["median_mbps"], s=size[g["one_tile"]], facecolor="none",
               edgecolor=color, linewidth=1.4, zorder=2)
    mid = g["median_mbps"].median()
    ax.axhline(mid, color=style.MUTED, linewidth=1, linestyle="--", zorder=1)
    ax.text(0.99, mid + 6, f"middle county {mid:.0f}", transform=ax.get_yaxis_transform(), ha="right",
            va="bottom", fontsize=8.5, color=style.MUTED)
    for _, r in g[g["county"].isin(LABEL[kind])].iterrows():
        dx, dy, ha = LABEL[kind][r["county"]]
        name = r["county"] + (" (one tile)" if r["one_tile"] else "")
        ax.annotate(name, (r["median_hh_income"], r["median_mbps"]), xytext=(dx, dy), textcoords="offset points",
                    ha=ha, va="center", fontsize=8.5, color=style.FG2,
                    arrowprops=dict(arrowstyle="-", color=style.MUTED, linewidth=0.6, shrinkA=2, shrinkB=4))
    ax.set_title(f"{kind.capitalize()} tiles: {len(g)} counties, rank correlation {rho[kind]:.2f}",
                 fontsize=11, loc="left")
    ax.xaxis.set_major_locator(MultipleLocator(20_000))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v / 1000:.0f}k"))
    ax.set_xlabel(f"Median household income (ACS 5-year, {ACS})")
axes[0].set_ylabel(f"Median download, Mbps (Q{QUARTER} {YEAR})")
fig.suptitle("Income barely predicts speed, fixed or mobile, Texas counties", x=0.01, ha="left",
             fontsize=14, fontweight="bold", color=style.FG)
style.credit(fig, text=style.OOKLA_CREDIT + f" (fixed and mobile tiles, Q{QUARTER} {YEAR}).\n"
             f"Income: US Census Bureau ACS 5-year, table B19013. Counties with {MIN_TESTS['fixed']:,}+ fixed "
             f"or {MIN_TESTS['mobile']:,}+ mobile tests; medians from tile averages; dot size = tests;\nhollow = one tile holds over half the county's tests.")
style.save(fig, HERE / "charts" / "fixed-vs-mobile-income")
