"""Download NOAA Storm Events records for Hurricane Beryl in Texas (July 2024).

NOAA's Storm Events Database logs each weather event by county with start/end
times and damage estimates. We keep Texas events from July 7-10, 2024.

Usage (from data-stories/):
    pip install requests pandas
    python3 beryl/fetch_noaa.py

Writes data/beryl/noaa_storm_events_tx_2024-07.csv
Source: NOAA NCEI Storm Events Database, https://www.ncdc.noaa.gov/stormevents/
"""
import re
from io import BytesIO
from pathlib import Path

import pandas as pd
import requests

BASE = "https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/"
OUT = Path(__file__).resolve().parent.parent / "data" / "beryl"
OUT.mkdir(parents=True, exist_ok=True)

listing = requests.get(BASE, timeout=60).text
files = sorted(set(re.findall(r'StormEvents_details-ftp_v1\.0_d2024_c\d+\.csv\.gz', listing)))
if not files:
    raise SystemExit("Couldn't find the 2024 details file in the NOAA listing.")
print("Using", files[-1])
raw = requests.get(BASE + files[-1], timeout=300).content
df = pd.read_csv(BytesIO(raw), compression="gzip", low_memory=False)

tx = df[(df["STATE"] == "TEXAS") & (df["BEGIN_YEARMONTH"] == 202407) & (df["BEGIN_DAY"].between(7, 10))]
keep = ["EVENT_ID", "EPISODE_ID", "CZ_TYPE", "CZ_FIPS", "CZ_NAME", "EVENT_TYPE", "BEGIN_DAY", "BEGIN_TIME",
        "END_DAY", "END_TIME", "DAMAGE_PROPERTY", "INJURIES_DIRECT", "DEATHS_DIRECT", "EPISODE_NARRATIVE"]
tx = tx[[c for c in keep if c in tx.columns]]
path = OUT / "noaa_storm_events_tx_2024-07.csv"
tx.to_csv(path, index=False)
print(f"{len(tx):,} Texas events, July 7-10 2024 -> {path}")
print(tx["EVENT_TYPE"].value_counts().head(10).to_string())
