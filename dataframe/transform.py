# adstoolbox[dataframe] or adstoolbox[pgsql/mssql/mysql] installe polars
import polars as pl

tbl = [
    ("A A A A", "1"),
    ("B   V", "2"),
    ("CZZ  ZDQS", "3"),
    ("CQSD d", "4"),
    ("CDAS   AZDASD", "5")
]
df = pl.DataFrame(tbl, schema=["key", "value"], orient="row")
print(df)

# Suppression des espaces sur une colonne
df = df.with_columns(pl.col("key").str.replace_all(" ", ""))
print(df)

# Concaténation de 2 champs
df = df.with_columns(pl.concat_str(["key", "value"], separator="-").alias("value2"))
print(df)
