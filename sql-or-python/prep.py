"""Step 0 (shared): put every tile in a Texas county.

Both the SQL and the pandas versions start from the same table, so this step
lives on its own. It takes the tile centroids from tools/fetch_ookla.py and
does a point-in-polygon join against Census county boundaries.

Input:  ../data/texas_fixed_2025.parquet   (from tools/fetch_ookla.py)
        ../data/us_counties.geojson         (Census 2010 county boundaries, via plotly/datasets)
Output: ../data/tx_tiles_by_county.parquet
"""
from pathlib import Path

import geopandas as gpd
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
COUNTIES_URL = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"

counties_path = DATA / "us_counties.geojson"
counties = gpd.read_file(counties_path if counties_path.exists() else COUNTIES_URL)
tx = counties.loc[counties["STATE"] == "48", ["id", "NAME", "geometry"]]
tx = tx.rename(columns={"id": "county_fips", "NAME": "county"}).to_crs("EPSG:4326")

tiles = pd.read_parquet(DATA / "texas_fixed_2025.parquet")
points = gpd.GeoDataFrame(
    tiles, geometry=gpd.points_from_xy(tiles["tile_x"], tiles["tile_y"]), crs="EPSG:4326"
)

joined = gpd.sjoin(points, tx, predicate="within", how="inner")
out = pd.DataFrame(joined.drop(columns=["geometry", "index_right"]))
out.to_parquet(DATA / "tx_tiles_by_county.parquet", index=False)

dropped = len(tiles) - len(out)
print(f"{len(out):,} tiles in {out['county_fips'].nunique()} Texas counties "
      f"({dropped:,} bounding-box tiles fell outside Texas and were dropped)")
