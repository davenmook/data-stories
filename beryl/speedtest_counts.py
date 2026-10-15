"""Did speed test counts notice Hurricane Beryl? (Spoiler: not at quarterly resolution.)

Compares how many Ookla speed tests were taken in the Houston area from Q2 to Q3
(Beryl hit July 8, 2024, so its outage falls inside Q3), against the same change a
year earlier and against the rest of Texas.

Houston area here = 11 counties around Houston that took the brunt of the storm:
Harris, Fort Bend, Montgomery, Brazoria, Galveston, Waller, Liberty, Chambers,
Matagorda, Wharton and Austin.

Input:  ../data/texas_fixed_2023.parquet, ../data/texas_fixed_2024.parquet  (tools/fetch_ookla.py)
        ../data/us_counties.geojson (downloaded automatically if missing)
Output: ../data/beryl/speedtest_q2_q3.csv
        ../data/beryl/speedtest_q2_q3_by_speed_houston.csv
        charts/speedtest-q2-q3.{svg,png}, charts/speedtest-by-speed.{svg,png}
"""
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
sys.path.insert(0, str(HERE.parent / "tools"))
import style  # noqa: E402

HOUSTON = ["Harris", "Fort Bend", "Montgomery", "Brazoria", "Galveston", "Waller", "Liberty",
           "Chambers", "Matagorda", "Wharton", "Austin"]
COUNTIES_URL = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"

path = DATA / "us_counties.geojson"
counties = gpd.read_file(path if path.exists() else COUNTIES_URL)
tx = counties.loc[counties["STATE"] == "48", ["NAME", "geometry"]].rename(columns={"NAME": "county"}).to_crs("EPSG:4326")

rows = []
for year in (2023, 2024):
    t = pd.read_parquet(DATA / f"texas_fixed_{year}.parquet")
    pts = gpd.GeoDataFrame(t, geometry=gpd.points_from_xy(t["tile_x"], t["tile_y"]), crs="EPSG:4326")
    j = gpd.sjoin(pts, tx, predicate="within", how="inner")
    j["area"] = np.where(j["county"].isin(HOUSTON), "Houston area", "Rest of Texas")
    q = j[j["quarter"].isin([2, 3])].groupby(["area", "quarter"])["tests"].sum().unstack()
    for area, r in q.iterrows():
        rows.append({"year": year, "area": area, "q2_tests": int(r[2]), "q3_tests": int(r[3]),
                     "change_pct": round((r[3] / r[2] - 1) * 100, 1)})

out = pd.DataFrame(rows)
(DATA / "beryl").mkdir(parents=True, exist_ok=True)
out.to_csv(DATA / "beryl" / "speedtest_q2_q3.csv", index=False)
print(out.to_string(index=False))

c = out.set_index(["area", "year"])["change_pct"]
did = (c["Houston area", 2024] - c["Houston area", 2023]) - (c["Rest of Texas", 2024] - c["Rest of Texas", 2023])
print(f"\nHouston's year-over-year jump beyond the rest of Texas: {did:+.1f} points")

style.use()
fig, ax = plt.subplots(figsize=(8, 4.4))
x = np.arange(2)
for k, (area, color) in enumerate((("Houston area", style.TEAL), ("Rest of Texas", style.NEUTRAL))):
    vals = [c[area, 2023], c[area, 2024]]
    bars = ax.bar(x + (k - 0.5) * 0.36, vals, width=0.34, color=color, label=area)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + (0.6 if v >= 0 else -0.6), f"{v:+.1f}%",
                ha="center", va="bottom" if v >= 0 else "top", fontsize=10, color=style.FG)
ax.axhline(0, color=style.MUTED, linewidth=1)
ax.set_xticks(x, ["2023 (no hurricane)", "2024 (Beryl, Jul 8)"])
ax.set_ylabel("Change in speed tests, Q2 to Q3")
ax.set_title("Speed tests from Q2 to Q3: Houston area vs the rest of Texas")
ax.legend(loc="upper left")
ax.grid(axis="x", visible=False)
style.credit(fig, text=style.OOKLA_CREDIT + ".\nHouston area = 11 counties around Houston.")
style.save(fig, HERE / "charts" / "speedtest-q2-q3")

# ---- By speed bin: did Beryl push tests into the slow bins? ----
# Each tile is binned by its average download speed that quarter. Tiles can move between
# bins as networks get faster, so this shows where tests landed, not the same tiles over time.
BINS = [0, 25, 100, 250, 500, float("inf")]
LABELS = ["Under 25", "25-100", "100-250", "250-500", "500+"]
brow = []
for year in (2023, 2024):
    t = pd.read_parquet(DATA / f"texas_fixed_{year}.parquet")
    t = t[t["quarter"].isin([2, 3])]
    pts = gpd.GeoDataFrame(t, geometry=gpd.points_from_xy(t["tile_x"], t["tile_y"]), crs="EPSG:4326")
    j = gpd.sjoin(pts, tx, predicate="within", how="inner")
    j = j[j["county"].isin(HOUSTON)]
    j["speed_bin"] = pd.cut(j["avg_d_kbps"] / 1000, bins=BINS, labels=LABELS, right=False)
    q = j.groupby(["speed_bin", "quarter"], observed=True)["tests"].sum().unstack()
    for b, r in q.iterrows():
        brow.append({"year": year, "speed_bin_mbps": b, "q2_tests": int(r[2]), "q3_tests": int(r[3]),
                     "change_pct": round((r[3] / r[2] - 1) * 100, 1)})
bins_df = pd.DataFrame(brow)
bins_df.to_csv(DATA / "beryl" / "speedtest_q2_q3_by_speed_houston.csv", index=False)
print("\nHouston area, Q2 to Q3 change in tests by tile speed (Mbps):")
print(bins_df.pivot(index="speed_bin_mbps", columns="year", values="change_pct").loc[LABELS].to_string())

fig, ax = plt.subplots(figsize=(9, 4.4))
x = np.arange(len(LABELS))
for k, (year, color) in enumerate(((2023, style.NEUTRAL), (2024, style.TEAL))):
    v = bins_df[bins_df["year"] == year].set_index("speed_bin_mbps").loc[LABELS, "change_pct"].to_numpy()
    bars = ax.bar(x + (k - 0.5) * 0.38, v, width=0.36, color=color, label=str(year))
    for b, val in zip(bars, v):
        ax.text(b.get_x() + b.get_width() / 2, val + (1 if val >= 0 else -1), f"{val:+.0f}%", ha="center",
                va="bottom" if val >= 0 else "top", fontsize=9, color=style.FG)
ax.axhline(0, color=style.MUTED, linewidth=1)
ax.set_xticks(x, [f"{l} Mbps" for l in LABELS])
ax.set_ylabel("Change in speed tests, Q2 to Q3")
ax.set_title("Houston area: where the Q3 speed tests landed, by tile speed")
ax.legend(loc="upper left")
ax.grid(axis="x", visible=False)
style.credit(fig, text=style.OOKLA_CREDIT + ".\nTiles binned by average download speed each quarter.")
style.save(fig, HERE / "charts" / "speedtest-by-speed")
