"""Download IODA internet outage signals for Texas around Hurricane Beryl.

IODA (Internet Outage Detection and Analysis, Georgia Tech) tracks how reachable
each region's internet is, using three independent signals:
  - bgp:    how many network routes (prefixes) are announced from the region
  - ping-slash24: how many /24 address blocks answer active probes
  - merit-nt: unsolicited "background" traffic seen by a network telescope
When power goes out, all three tend to drop.

Usage (from data-stories/):
    pip install requests pandas
    python3 beryl/fetch_ioda.py

Writes data/beryl/ioda_texas_2024-07.csv (and the same window in 2023 as a baseline).
Source: IODA, https://ioda.inetintel.cc.gatech.edu (cite in the post).
"""
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

API = "https://api.ioda.inetintel.cc.gatech.edu/v2"
OUT = Path(__file__).resolve().parent.parent / "data" / "beryl"
OUT.mkdir(parents=True, exist_ok=True)
WINDOWS = {  # Beryl landfall: July 8, 2024, early morning, Matagorda Bay
    "2024-07": ("2024-07-01", "2024-07-22"),
    "2023-07": ("2023-07-01", "2023-07-22"),  # same weeks a year earlier, no hurricane
}


def ts(day):
    return int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp())


def find_texas():
    r = requests.get(f"{API}/entities/query", params={"entityType": "region", "search": "Texas"}, timeout=60)
    r.raise_for_status()
    hits = r.json().get("data", [])
    for h in hits:
        attrs = h.get("attrs") or {}
        if "United States" in str(attrs.get("country_name", "")) or attrs.get("country_code") == "US":
            return h["code"], h["name"]
    print("Couldn't pick Texas automatically. Candidates:")
    for h in hits:
        print("  ", h.get("code"), h.get("name"), h.get("attrs"))
    raise SystemExit("Set the code by hand in this script and rerun.")


code, name = find_texas()
print(f"IODA region: {name} (code {code})")

for label, (start, end) in WINDOWS.items():
    r = requests.get(f"{API}/signals/raw/region/{code}",
                     params={"from": ts(start), "until": ts(end)}, timeout=120)
    r.raise_for_status()
    rows = []
    for series_group in r.json().get("data", []):
        for s in series_group:
            t0, step = s["from"], s["step"]
            for i, v in enumerate(s["values"] or []):
                rows.append({"datasource": s["datasource"], "time_utc": datetime.fromtimestamp(t0 + i * step, timezone.utc),
                             "value": v})
    df = pd.DataFrame(rows)
    path = OUT / f"ioda_texas_{label}.csv"
    df.to_csv(path, index=False)
    print(f"{label}: {len(df):,} points across {df['datasource'].nunique() if len(df) else 0} signals -> {path}")
    time.sleep(1)
