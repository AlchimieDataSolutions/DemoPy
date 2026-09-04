# adstoolbox[dataframe]  (ou tout extra de base : mssql, mysql, pgsql)
"""
Polars : les manipulations utiles avec adsToolBox.

Ce script n'utilise PAS adsToolBox, seulement Polars. Il est ici parce que
Pipeline, DataFactory et DataComparator produisent et consomment des
DataFrames Polars : savoir les manipuler est indispensable pour exploiter
leurs sorties.

Polars n'est pas une dépendance du cœur. Il arrive avec l'extra `dataframe`,
ou avec n'importe quel extra de base de données qui l'inclut.
"""
import polars as pl

# ---------------------------------------------------------------------------
# 0. Construire un DataFrame depuis des lignes
# ---------------------------------------------------------------------------
# orient="row" est OBLIGATOIRE quand on part d'une liste de tuples : sans lui
# Polars interprète chaque tuple comme une COLONNE et le résultat est
# transposé. C'est la forme que renvoient les curseurs SQL, donc celle que
# vous manipulerez en sortie de sql_query.
tbl = [
    ("A", "5"),
    ("C", "3"),
    ("E", "1"),
    ("D", "2"),
    ("B", "4"),
]
df = pl.DataFrame(
    tbl,
    schema=["key", "value"],
    orient="row",
)
print(df)

# Piège de typage : ici "value" contient des CHAÎNES, pas des entiers, parce
# que les tuples contiennent des str. Un tri sur cette colonne sera donc
# lexicographique ("10" < "9"). Convertissez si l'ordre numérique importe.
print(df.schema)

# ---------------------------------------------------------------------------
# 1. Trier
# ---------------------------------------------------------------------------
print(df.sort("key"))
print(df.sort("value"))

# descending et nulls_last rendent l'intention explicite.
print(df.sort("value", descending=True, nulls_last=True))

# Tri multi-colonnes : une liste de colonnes, et autant de sens de tri.
print(df.sort(["key", "value"], descending=[False, True]))

# ---------------------------------------------------------------------------
# 2. Dédoublonner
# ---------------------------------------------------------------------------
tbl_doublons = [
    ("A", "1"),
    ("B", "2"),
    ("C", "3"),
    ("C", "3"),
    ("C", "3"),
]
df_doublons = pl.DataFrame(tbl_doublons, schema=["key", "value"], orient="row")

# unique() sans argument compare TOUTES les colonnes.
print(df_doublons.unique())

# ATTENTION : unique() ne garantit pas l'ordre des lignes. Avec
# maintain_order=True l'ordre d'origine est conservé, au prix d'un tri.
print(df_doublons.unique(maintain_order=True))

# subset restreint la comparaison à certaines colonnes, keep choisit la ligne
# retenue : "first", "last", "any" (le plus rapide) ou "none" (élimine tous
# les doublons, y compris la première occurrence).
print(df_doublons.unique(subset=["key"], keep="first", maintain_order=True))

# Pour dédoublonner un transfert par empreinte plutôt que par comparaison de
# colonnes, voir pipeline/pipeline_hash.py.

# ---------------------------------------------------------------------------
# 3. Jointures
# ---------------------------------------------------------------------------
df1 = pl.DataFrame(
    [("A", "1"), ("B", "2"), ("C", "3"), ("D", "4")],
    schema=["key", "value1"],
    orient="row",
)
df2 = pl.DataFrame(
    [("A", "10"), ("B", "20"), ("C", "40")],
    schema=["key", "value2"],
    orient="row",
)

# inner : seules les clés présentes des deux côtés. "D" disparaît.
print(df1.join(df2, on="key", how="inner"))

# left : toutes les lignes de gauche, value2 à null quand la clé manque.
print(df1.join(df2, on="key", how="left"))

# full : l'union des deux côtés.
print(df1.join(df2, on="key", how="full"))

# anti : les lignes de gauche SANS correspondance à droite. C'est la
# jointure la plus utile pour un contrôle de cohérence — elle répond à
# "qu'est-ce qui manque à droite ?" en une opération.
print(df1.join(df2, on="key", how="anti"))

# semi : les lignes de gauche QUI ont une correspondance, sans ramener les
# colonnes de droite. Un filtre par appartenance.
print(df1.join(df2, on="key", how="semi"))

# Clés de noms différents : left_on / right_on au lieu de on.
print(df1.join(df2.rename({"key": "cle"}), left_on="key", right_on="cle", how="inner"))

# ---------------------------------------------------------------------------
# 4. Valeurs nulles
# ---------------------------------------------------------------------------
tbl_nuls = [
    ("A", "5"),
    (None, "3"),
    ("E", "1"),
    ("D", "2"),
    ("B", None),
]
df_nuls = pl.DataFrame(tbl_nuls, schema=["key", "value"], orient="row")
print(df_nuls)

# fill_null avec une valeur littérale remplit TOUTES les colonnes.
print(df_nuls.fill_null("C"))

# Par colonne, avec des valeurs différentes : passez par with_columns.
print(df_nuls.with_columns(
    pl.col("key").fill_null("INCONNU"),
    pl.col("value").fill_null("0"),
))

# Compter les nuls avant de décider : indispensable en contrôle qualité.
print(df_nuls.null_count())

# Supprimer les lignes incomplètes plutôt que les remplir.
print(df_nuls.drop_nulls())
print(df_nuls.drop_nulls(subset=["key"]))

# Rappel important pour Pipeline : une colonne entièrement nulle est typée
# pl.Null, un type qui ne correspond à aucune colonne SQL. Pipeline gère ce
# cas par réinférence sur les batchs suivants — voir
# pipeline/polars_inference.py.

# ---------------------------------------------------------------------------
# 5. Transformer des colonnes
# ---------------------------------------------------------------------------
tbl_texte = [
    ("A A A A", "1"),
    ("B   V", "2"),
    ("CZZ  ZDQS", "3"),
    ("CQSD d", "4"),
    ("CDAS   AZDASD", "5"),
]
df_texte = pl.DataFrame(tbl_texte, schema=["key", "value"], orient="row")
print(df_texte)

# Supprimer les espaces d'une colonne.
print(df_texte.with_columns(pl.col("key").str.replace_all(" ", "")))

# Concaténer deux champs dans une nouvelle colonne.
print(df_texte.with_columns(
    pl.concat_str(["key", "value"], separator="-").alias("value2"),
))

# with_columns AJOUTE ou REMPLACE selon le nom : sans alias, la colonne
# d'origine est écrasée. Nommez explicitement pour conserver les deux.
print(df_texte.with_columns(
    pl.col("key").str.to_uppercase().alias("key_majuscules"),
))

# Convertir un type. strict=False met à null ce qui n'est pas convertible
# au lieu de lever une exception : à réserver aux données douteuses, car
# l'échec devient alors silencieux.
print(df_texte.with_columns(pl.col("value").cast(pl.Int64, strict=False)))

# Plusieurs transformations en un seul with_columns : Polars les évalue en
# parallèle, ce qui est plus rapide que des appels enchaînés.
print(df_texte.with_columns(
    pl.col("key").str.replace_all(" ", "").alias("key_compact"),
    pl.col("value").cast(pl.Int64, strict=False).alias("value_int"),
))