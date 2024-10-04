import polars as pl

data = [
    ("A", 1, 10.5, 'He said "Hello"'),
    ("B", 2, 20.1, "NA"),
    ("C", 3, 30.7, "NA"),
    ("D", "NA", 40.6, "NA")
]
df = pl.DataFrame(data, schema=["key", "value1", "value2", "value3"], orient="row")

# Écriture dans un fichier csv
csv_file = "example_data.csv"
df.write_csv(csv_file, separator=";", quote_char='"', include_header=True)

# Lecture à partir d'un fichier csv
df_csv = pl.read_csv(
    "example_data.csv",
    separator=";",  #Utiliser un séparateur précis, par défaut ","
    has_header=True,  #Indique si le fichier a une ligne d'en-tête
    null_values=["NA"],  #Interpréter ces valeurs comme nulles
    columns=["key", "value1", "value3"],  #Lire uniquement certaines colonnes
    quote_char='"'  #Le caractère utilisé pour entourer les valeurs est le double guillemet
)
print(df_csv)