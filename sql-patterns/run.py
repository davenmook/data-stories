"""Run each block in patterns.sql and print its result.

Usage (from sql-patterns/): python3 run.py
"""
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
blocks = HERE.joinpath("patterns.sql").read_text().split("-- name: ")[1:]

con = duckdb.connect()
con.execute(f"SET file_search_path = '{HERE}'")
for block in blocks:
    title, sql = block.split("\n", 1)
    print(f"\n== {title}")
    print(con.sql(sql))
