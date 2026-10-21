"""Download the FCC's Hurricane Beryl status reports and pull out cell sites down by county.

When a big storm hits, the FCC turns on DIRS (the Disaster Information Reporting
System). Phone, cable and wireless companies report what's down, and the FCC posts
a daily "Communications Status Report" with a table of cell sites out of service
by county. For Beryl that ran from July 8 to mid-July 2024.

The reports are PDFs, so this script:
  1. finds the Beryl status reports linked from https://www.fcc.gov/beryl
     (plus the July 9 report, whose address we know, in case the page changes),
  2. saves each PDF to data/beryl/dirs/,
  3. reads the county table out of each one into a single tidy CSV.

Usage (from data-stories/):
    pip install requests pandas pdfplumber
    python3 beryl/fetch_dirs.py
    python3 beryl/fetch_dirs.py --pdf path/to/report.pdf ...   # already have the PDFs? skip the download

Writes data/beryl/dirs/*.pdf and data/beryl/fcc_dirs_cell_sites_tx_2024-07.csv
(one row per report date and county: sites served, sites out, percent out).

Source: Federal Communications Commission, Disaster Information Reporting System
(DIRS), Communications Status Reports for Areas Impacted by Hurricane Beryl,
July 2024. https://www.fcc.gov/beryl  (US government work, public domain)
"""
import argparse
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd

HUB = "https://www.fcc.gov/beryl"
KNOWN = ["https://docs.fcc.gov/public/attachments/DOC-403846A1.pdf"]  # July 9, 2024 report
OUT = Path(__file__).resolve().parent.parent / "data" / "beryl"
PDF_DIR = OUT / "dirs"
CSV = OUT / "fcc_dirs_cell_sites_tx_2024-07.csv"
HEADERS = {"User-Agent": "data-stories (github.com/davenmook/data-stories)"}

# A county row looks like "Harris 1,234 567 45.9%" (sometimes with "TX" or "Texas" in front).
ROW = re.compile(r"^(?:TX\s+|Texas\s+)?([A-Z][A-Za-z.' ]+?)\s+(\d[\d,]*)\s+(\d[\d,]*)\s+(\d{1,3}(?:\.\d+)?)\s*%$")
DATE = re.compile(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s*(20\d\d)")
SKIP = {"Total", "Totals", "State", "County", "Grand Total"}


def find_report_urls(session):
    """Follow the Beryl hub to each status report page, then to its PDF attachments."""
    html = session.get(HUB, timeout=60).text
    pages = sorted({urljoin(HUB, h) for h in re.findall(r'href="([^"]+)"', html)
                    if "status-report" in h.lower() or "comms-status" in h.lower()})
    pdfs = []
    for page in pages:
        time.sleep(1)  # be polite
        body = session.get(page, timeout=60).text
        pdfs += [urljoin(page, h) for h in re.findall(r'href="([^"]+?A1\.pdf)"', body)]
    return sorted(set(pdfs) | set(KNOWN))


def download(urls):
    import requests
    s = requests.Session()
    s.headers.update(HEADERS)
    if not urls:
        try:
            urls = find_report_urls(s)
        except requests.RequestException as e:
            print(f"Couldn't read {HUB} ({e}); falling back to the report we know about.")
            urls = KNOWN
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    for url in urls:
        path = PDF_DIR / url.rsplit("/", 1)[-1]
        if not path.exists():
            try:
                r = s.get(url, timeout=120)
                r.raise_for_status()
            except requests.RequestException as e:
                raise SystemExit(f"Couldn't download {url} ({e}).\n"
                                 "Save it from a browser instead, then run: python3 beryl/fetch_dirs.py --pdf <file.pdf>")
            path.write_bytes(r.content)
            time.sleep(1)
        print("Got", path.name)
        paths.append(path)
    return paths


def parse_text(text):
    """Turn one report's text into (report_date, rows). Only the cell-site-by-county table matches ROW."""
    m = DATE.search(text)
    report_date = datetime.strptime(" ".join(m.groups()), "%B %d %Y").date() if m else None
    rows = []
    for line in text.splitlines():
        hit = ROW.match(line.strip())
        if not hit:
            continue
        county, served, out, pct = hit.groups()
        county = county.strip()
        if county in SKIP:
            continue
        served, out = int(served.replace(",", "")), int(out.replace(",", ""))
        if out > served:  # not a cell-site row
            continue
        rows.append({"report_date": report_date, "county": county, "cell_sites_served": served,
                     "cell_sites_out": out, "pct_out": float(pct)})
    return report_date, rows


def parse_pdf(path):
    import pdfplumber
    with pdfplumber.open(path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    return parse_text(text)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pdf", nargs="*", type=Path, help="parse these PDFs instead of downloading")
    ap.add_argument("--url", nargs="*", default=[], help="download these report PDFs instead of searching")
    args = ap.parse_args()

    paths = args.pdf if args.pdf else download(args.url)
    rows = []
    for path in paths:
        day, found = parse_pdf(path)
        print(f"{path.name}: report date {day}, {len(found)} county rows")
        rows += [dict(r, source_file=path.name) for r in found]
    if not rows:
        raise SystemExit("No county rows found. Open a PDF and check the table layout against ROW in this script.")

    df = pd.DataFrame(rows).drop_duplicates(["report_date", "county"]).sort_values(["report_date", "pct_out"],
                                                                                  ascending=[True, False])
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(CSV, index=False)
    print(f"\n{len(df):,} rows -> {CSV}")
    first = df[df["report_date"] == df["report_date"].min()]
    print(f"\nWorst counties on {first['report_date'].iloc[0]}:")
    print(first.head(10)[["county", "cell_sites_served", "cell_sites_out", "pct_out"]].to_string(index=False))


if __name__ == "__main__":
    main()
