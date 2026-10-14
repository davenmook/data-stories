"""Run both versions and prove they give the same answer."""
from pathlib import Path

import duckdb
import pandas as pd

from in_pandas import county_medians

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"

sql = duckdb.sql((HERE / "in_sql.sql").read_text()).df()
py = county_medians(pd.read_parquet(DATA / "tx_tiles_by_county.parquet"))

sql = sql[py.columns].astype(py.dtypes.to_dict())
pd.testing.assert_frame_equal(sql, py, check_exact=False, rtol=1e-9)
print(f"Match: SQL and pandas agree on all {len(py):,} county-quarter rows.")

py.to_csv(DATA / "tx_county_medians_2025.csv", index=False)
