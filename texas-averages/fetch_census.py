"""Download median household income for every Texas county from the Census ACS.

Uses the Census Data API and only the Python standard library, so it runs in a plain
python3 with nothing installed. The API wants a free key: sign up at
https://api.census.gov/data/key_signup.html, then set it for this Terminal window
(keep it out of the repo):
    export CENSUS_API_KEY=your_key_here

Usage:
    python3 fetch_census.py          # ACS 5-year 2024, or the newest of 2023/2022 that answers
    python3 fetch_census.py 2023     # any other ACS 5-year release

Output: ../data/tx_county_income_acs<YEAR>.csv
        county_fips, county, median_hh_income, moe   (moe = margin of error, 90%)

Data: US Census Bureau, American Community Survey 5-year estimates, table B19013
(median household income in the past 12 months, inflation-adjusted dollars).
https://www.census.gov/programs-surveys/acs
"""
import csv
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ASKED = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
KEY = os.environ.get("CENSUS_API_KEY", "").strip()
if not KEY:
    raise SystemExit("Set CENSUS_API_KEY first (free key: https://api.census.gov/data/key_signup.html), "
                     "then run: export CENSUS_API_KEY=your_key_here")


def fetch(year):
    """Return the API's rows for one ACS 5-year release, or None if it isn't there."""
    url = (f"https://api.census.gov/data/{year}/acs/acs5"
           f"?get=NAME,B19013_001E,B19013_001M&for=county:*&in=state:48&key={KEY}")
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            body = r.read().decode("utf-8", "replace")
            status = r.status
    except urllib.error.HTTPError as e:
        body, status = e.read().decode("utf-8", "replace"), e.code
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        if "Missing Key" in body or "Invalid Key" in body:
            raise SystemExit("Census didn't accept the key. Check CENSUS_API_KEY (new keys can take a few minutes).")
        print(f"ACS {year}: no data (HTTP {status}). The API said: {body.strip()[:300] or '(empty reply)'}")
        return None


for YEAR in range(ASKED, ASKED - 3, -1):
    data = fetch(YEAR)
    if data:
        break
else:
    raise SystemExit("No ACS 5-year release worked. Paste the messages above to Claude.")

header, *rows = data
OUT = Path(__file__).resolve().parent.parent / "data" / f"tx_county_income_acs{YEAR}.csv"

col = {name: i for i, name in enumerate(header)}
OUT.parent.mkdir(parents=True, exist_ok=True)
kept = skipped = 0
with OUT.open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["county_fips", "county", "median_hh_income", "moe"])
    for r in rows:
        income = int(r[col["B19013_001E"]])
        if income < 0:  # Census uses big negative numbers for "no estimate"
            skipped += 1
            continue
        name = r[col["NAME"]].replace(" County, Texas", "")
        w.writerow([r[col["state"]] + r[col["county"]], name, income, int(r[col["B19013_001M"]])])
        kept += 1

print(f"Wrote {OUT.name} (ACS 5-year {YEAR}): {kept} Texas counties ({skipped} without an estimate)")
