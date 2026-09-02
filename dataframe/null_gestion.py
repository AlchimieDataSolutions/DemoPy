# adstoolbox[dataframe] or adstoolbox[pgsql/mssql/mysql] installe polars
import polars as pl

tbl = [
    ("A", "5"),
    (None, "3"),
    ("E", "1"),
    ("D", "2"),
    ("B", None)
]
df = pl.DataFrame(tbl, schema=["key", "value"], orient="row")
print(df)

df = df.fill_null("C")
print(df)