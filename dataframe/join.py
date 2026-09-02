# adstoolbox[dataframe] or adstoolbox[pgsql/mssql/mysql] installe polars
import polars as pl

tbl1 = [
    ("A", "1"),
    ("B", "2"),
    ("C", "3"),
    ("D", "4")
]

df1 = pl.DataFrame(tbl1, schema=["key", "value1"], orient="row")
tbl2 = [
    ("A", "10"),
    ("B", "20"),
    ("C", "40"),
]

df2 = pl.DataFrame(tbl2, schema=["key", "value2"], orient="row")

# Inner join
df_joined = df1.join(df2, on="key", how="inner")
print(df_joined)

# Left join
df_left_joined = df1.join(df2, on="key", how="left")
print(df_left_joined)
