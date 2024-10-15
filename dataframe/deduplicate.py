import polars as pl

tbl = [
    ("A", "1"),
    ("B", "2"),
    ("C", "3"),
    ("C", "3"),
    ("C", "3")
]

df = pl.DataFrame(tbl, schema=["key", "value"], orient="row")

df = df.unique()

print(df)
