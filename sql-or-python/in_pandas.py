"""Median download speed by Texas county and quarter, in pandas.

Same question and same two medians as in_sql.sql.
"""
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"


def county_medians(tiles: pd.DataFrame) -> pd.DataFrame:
    df = tiles.assign(d_mbps=tiles["avg_d_kbps"] / 1000.0)
    keys = ["quarter", "county_fips"]

    # Plain median: every tile counts once
    out = df.groupby(keys).agg(
        county=("county", "first"),
        tiles=("d_mbps", "size"),
        tests=("tests", "sum"),
        median_tile_mbps=("d_mbps", "median"),
    )

    # Weighted median: sort slowest first, keep a running total of tests,
    # take the first tile that passes half of all tests
    df = df.sort_values(keys + ["d_mbps", "quadkey"])
    running = df.groupby(keys)["tests"].cumsum()
    total = df.groupby(keys)["tests"].transform("sum")
    out["weighted_median_mbps"] = df[running >= total / 2].groupby(keys)["d_mbps"].min()

    return out.reset_index().sort_values(keys).reset_index(drop=True)


if __name__ == "__main__":
    result = county_medians(pd.read_parquet(DATA / "tx_tiles_by_county.parquet"))
    print(result.head(10).to_string(index=False))
