"""Did phones pick up the slack after Beryl? Mobile speed tests, Q2 to Q3, Texas metros.

Idea: when home power and Wi-Fi go out, people move to cellular. If that happened at
scale, the Houston area should show more mobile tests and slower mobile speeds in Q3
2024, beyond what other Texas metros show and beyond Houston's own change in 2023.

Mean speed is exact (each tile's average weighted by its tests). Caveats: quarterly tiles
blur a week-long event, slower speeds can also come from storm-damaged cell sites (the
data can't tell those apart), and total mobile test volume in the open data changes a lot
between years, so compare changes, not raw counts.

Input:  ../data/texas_mobile_2023.parquet, ../data/texas_mobile_2024.parquet
        (python3 tools/fetch_ookla.py 2024 mobile, and 2023)
Output: ../data/beryl/mobile_q2_q3_metros.csv
        charts/mobile-speed-metros.{svg,png}
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

METROS = {
    "Houston area": ["Harris", "Fort Bend", "Montgomery", "Brazoria", "Galveston", "Waller", "Liberty",
                     "Chambers", "Matagorda", "Wharton", "Austin"],
    "Dallas-Fort Worth": ["Dallas", "Tarrant", "Collin", "Denton"],
    "Austin": ["Travis", "Williamson"],
    "San Antonio": ["Bexar"],
    "El Paso": ["El Paso"],
}
COUNTIES_URL = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"

path = DATA / "us_counties.geojson"
counties = gpd.read_file(path if path.exists() else COUNTIES_URL)
tx = counties.loc[counties["STATE"] == "48", ["NAME", "geometry"]].rename(columns={"NAME": "county"}).to_crs("EPSG:4326")

rows = []
for year in (2023, 2024):
    t = pd.read_parquet(DATA / f"texas_mobile_{year}.parquet")
    t = t[t["quarter"].isin([2, 3])]
    pts = gpd.GeoDataFrame(t, geometry=gpd.points_from_xy(t["tile_x"], t["tile_y"]), crs="EPSG:4326")
    j = gpd.sjoin(pts, tx, predicate="within", how="inner")
    j["d_mbps"] = j["avg_d_kbps"] / 1000
    for metro, cs in METROS.items():
        m = j[j["county"].isin(cs)]
        q = m.groupby("quarter").apply(lambda df: pd.Series({
            "tests": df["tests"].sum(), "mean_mbps": (df["d_mbps"] * df["tests"]).sum() / df["tests"].sum()}),
            include_groups=False)
        rows.append({"metro": metro, "year": year,
                     "q2_tests": int(q.loc[2, "tests"]), "q3_tests": int(q.loc[3, "tests"]),
                     "tests_change_pct": round((q.loc[3, "tests"] / q.loc[2, "tests"] - 1) * 100, 1),
                     "q2_mean_mbps": round(q.loc[2, "mean_mbps"], 1), "q3_mean_mbps": round(q.loc[3, "mean_mbps"], 1),
                     "speed_change_pct": round((q.loc[3, "mean_mbps"] / q.loc[2, "mean_mbps"] - 1) * 100, 1)})

out = pd.DataFrame(rows)
out.to_csv(DATA / "beryl" / "mobile_q2_q3_metros.csv", index=False)
print(out.to_string(index=False))

style.use()
fig, ax = plt.subplots(figsize=(9, 4.6))
names = list(METROS)
x = np.arange(len(names))
for k, (year, color) in enumerate(((2023, style.NEUTRAL), (2024, style.TEAL))):
    v = out[out["year"] == year].set_index("metro").loc[names, "speed_change_pct"].to_numpy()
    bars = ax.bar(x + (k - 0.5) * 0.38, v, width=0.36, color=color, label=str(year))
    for b, val in zip(bars, v):
        ax.text(b.get_x() + b.get_width() / 2, val + (0.6 if val >= 0 else -0.6), f"{val:+.0f}%", ha="center",
                va="bottom" if val >= 0 else "top", fontsize=9, color=style.FG)
ax.axhline(0, color=style.MUTED, linewidth=1)
ax.set_xticks(x, names)
ax.set_ylabel("Change in mean mobile download, Q2 to Q3")
ax.set_title("Mobile speeds from Q2 to Q3: only Houston went backwards in 2024")
ax.legend(loc="upper left")
ax.grid(axis="x", visible=False)
style.credit(fig, text=style.OOKLA_CREDIT + " (mobile tiles).\nMetro areas by county; mean weighted by tests.")
style.save(fig, HERE / "charts" / "mobile-speed-metros")
