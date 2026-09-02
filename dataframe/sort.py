# adstoolbox[dataframe] or adstoolbox[pgsql/mssql/mysql] installe polars
import polars as pl

tbl = [
    ("A", "5"),
    ("C", "3"),
    ("E", "1"),
    ("D", "2"),
    ("B", "4")
]
df = pl.DataFrame(tbl, schema=["key", "value"], orient="row")

df = df.sort("key")
print(df)

df = df.sort("value")
print(df)
