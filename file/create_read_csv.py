# adstoolbox[dataframe]  (ou tout extra de base, qui installe polars)
# adstoolbox[files]      pour la section 4 seulement
"""
CSV : écriture et lecture avec Polars, en local et à distance.

Les sections 1 à 3 n'utilisent que Polars. La section 4 montre comment lire
un CSV situé sur un partage SMB ou un blob Azure en combinant FileHandler
et Polars, ce qu'aucun des deux ne fait seul.

    python file/create_read_csv.py
"""
import io
import os

import polars as pl

import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")

# ---------------------------------------------------------------------------
# 1. Écrire un CSV
# ---------------------------------------------------------------------------
# Le jeu contient volontairement un guillemet dans une valeur et des "NA"
# qui représentent des nuls : deux cas qui piègent la relecture.
data = [
    ("A", 1, 10.5, 'He said "Hello"'),
    ("B", 2, 20.1, "NA"),
    ("C", 3, 30.7, "NA"),
    ("D", "NA", 40.6, "NA"),
]
df = pl.DataFrame(
    data,
    schema=["key", "value1", "value2", "value3"],
    orient="row",
)

# Noter que value1 contient 1, 2, 3 puis la chaîne "NA" : la colonne est
# donc typée String, pas Int64. Polars n'échoue pas, il élargit le type.
print(df.schema)

csv_file = "file/example_data.csv"
df.write_csv(
    csv_file,
    separator=";",          # défaut ","
    quote_char='"',         # caractère d'encadrement
    include_header=True,
)

# La valeur contenant un guillemet est échappée automatiquement en le
# doublant, conformément au RFC 4180.
print(open(csv_file, encoding="utf-8").read())

# ---------------------------------------------------------------------------
# 2. Relire un CSV
# ---------------------------------------------------------------------------
df_csv = pl.read_csv(
    csv_file,
    separator=";",              # doit correspondre à l'écriture
    has_header=True,
    null_values=["NA"],         # ces valeurs deviennent des nuls
    columns=["key", "value1", "value3"],   # ne lit que ces colonnes
    quote_char='"',
)
print(df_csv)

# Effet de null_values : "NA" devient null, donc value1 ne contient plus que
# des entiers et Polars la type en Int64. Le type change entre l'écriture et
# la relecture — c'est normal, mais à savoir avant de comparer deux
# DataFrames avec check_dtypes=True (voir operations/compare.py).
print(df_csv.schema)

# ---------------------------------------------------------------------------
# 3. Forcer le typage plutôt que le subir
# ---------------------------------------------------------------------------
# schema_overrides impose le type d'une colonne sans toucher aux autres.
# Indispensable pour un identifiant à zéros de tête, que Polars
# transformerait en entier en perdant les zéros.
df_force = pl.read_csv(
    csv_file,
    separator=";",
    null_values=["NA"],
    schema_overrides={"value1": pl.String, "value2": pl.Float64},
)
print(df_force.schema)

# infer_schema_length limite le nombre de lignes examinées pour deviner les
# types. La valeur par défaut (100) suffit rarement sur un fichier dont les
# valeurs atypiques arrivent tard : mettre None force l'analyse complète, au
# prix d'un passage supplémentaire.
df_complet = pl.read_csv(csv_file, separator=";", infer_schema_length=None)
print(df_complet.schema)

# try_parse_dates convertit les colonnes qui ressemblent à des dates. Sans
# lui, une date reste une chaîne — cause fréquente de mauvaise surprise en
# alimentant un Pipeline.

# ---------------------------------------------------------------------------
# 4. Lire un CSV distant : FileHandler + Polars
# ---------------------------------------------------------------------------
# adstoolbox[files] à partir d'ici.
#
# Polars sait lire un chemin local, pas un partage SMB authentifié ni un
# blob Azure. FileHandler sait y accéder mais renvoie des octets. On combine
# les deux : FileHandler streame, io.BytesIO reconstitue un fichier en
# mémoire, Polars le lit.
local_f = ads.FileHandler(
    logger=logger,
    fs_url=None,          # ici en local, mais l'URL peut être smb:// ou az://
    batch_size=65_536,    # gros chunks : on assemble tout de suite après
)

contenu = b"".join(
    chunk if isinstance(chunk, bytes) else chunk.encode("utf-8")
    for chunk in local_f.read_file(file_path=csv_file, mode="rb")
)

df_distant = pl.read_csv(
    io.BytesIO(contenu),
    separator=";",
    null_values=["NA"],
)
print(df_distant)

# Limite de cette approche : le fichier passe INTÉGRALEMENT en mémoire. Pour
# un CSV de plusieurs gigaoctets sur un partage distant, transférez-le
# d'abord en local avec transfer_file, puis lisez-le avec pl.scan_csv qui
# travaille en flux. Voir file/transfer_file.py.

# Dans l'autre sens, pour écrire un CSV vers un partage distant :
csv_texte = df.write_csv(separator=";")   # sans chemin => renvoie une chaîne
local_f.write_file(
    file_path="file/example_export.csv",
    content=[csv_texte],
    mode="w",
)

local_f.remove_file(file_path="file/example_export.csv")