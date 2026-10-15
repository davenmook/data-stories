"""How much of Texas stopped answering when Hurricane Beryl hit (July 2024)?

Uses IODA's active probing signal ("ping-slash24"): every 10 minutes IODA pings
address blocks (/24s) across Texas and counts how many answer. When the power goes
out, home routers and small-business networks stop answering, so the count drops.

Each year is shown as a percent of its own normal (the median of July 1-7), with
the same weeks of 2023 as a no-hurricane baseline. Hourly medians, then a 3-hour
rolling median, smooth out short measurement glitches (one on July 6, 2024, two days
before landfall; one on July 12, 2023) while keeping drops that last several hours.

Input:  ../data/beryl/ioda_texas_2024-07.csv, ../data/beryl/ioda_texas_2023-07.csv  (fetch_ioda.py)
Output: ../data/beryl/ioda_hourly_pct.csv
        charts/texas-reachability.{svg,png}
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data" / "beryl"
sys.path.insert(0, str(HERE.parent / "tools"))
import style  # noqa: E402

TZ = "America/Chicago"
LANDFALL = pd.Timestamp("2024-07-08 04:00", tz=TZ)  # Matagorda Bay, early morning July 8


def hourly_pct(path, year):
    d = pd.read_csv(path, parse_dates=["time_utc"])
    s = d[d["datasource"] == "ping-slash24"].set_index("time_utc")["value"]
    base = s[: f"{year}-07-07"].median()
    h = (s / base * 100).resample("1h").median().rolling(3, center=True, min_periods=1).median().tz_convert(TZ)
    return h, base


y24, base24 = hourly_pct(DATA / "ioda_texas_2024-07.csv", 2024)
y23, base23 = hourly_pct(DATA / "ioda_texas_2023-07.csv", 2023)
y23.index = y23.index + pd.DateOffset(years=1)  # line up the same calendar days

out = pd.DataFrame({"pct_2024": y24, "pct_2023_same_days": y23}).loc["2024-07-05":"2024-07-17"]
out.round(2).to_csv(DATA / "ioda_hourly_pct.csv", index_label="hour_local")

after = y24[LANDFALL:]
low_day = y24["2024-07-08 10:00":"2024-07-09 11:00"]
print(f"Normal: {base24:,.0f} Texas /24 blocks answering (2023 same weeks: {base23:,.0f})")
print(f"Day after landfall: {low_day.median():.1f}% of normal "
      f"(about {base24 * (1 - low_day.median() / 100):,.0f} blocks quiet)")
for th in (95, 98, 99):
    t = after[(after >= th) & (after.index > LANDFALL + pd.Timedelta(hours=12))].index.min()
    print(f"Back to {th}%: {t:%a %b %d, %-I %p}")
print(f"2023 same weeks never dropped below {y23.loc['2024-07-05':'2024-07-17'].min():.1f}%")

style.use()
fig, ax = plt.subplots(figsize=(9, 4.4))
ax.plot(out.index, out["pct_2023_same_days"], color=style.NEUTRAL, linewidth=1.4, label="Same days in 2023")
ax.plot(out.index, out["pct_2024"], color=style.TEAL, linewidth=2, label="July 2024")
ax.axvline(LANDFALL, color=style.FG, linestyle="--", linewidth=1)
ax.text(LANDFALL, 100.6, " Beryl makes landfall", color=style.FG, fontsize=9, va="bottom")
ax.set_ylim(80, 101.5)
ax.set_ylabel("% of normal")
ax.set_title("Texas networks answering IODA's pings, July 2024")
ax.legend(loc="lower right")
ax.grid(axis="x", visible=False)
fig.autofmt_xdate()
style.credit(fig, text="Data: IODA (Internet Outage Detection and Analysis), Georgia Tech, active probing signal for Texas.")
style.save(fig, HERE / "charts" / "texas-reachability")
