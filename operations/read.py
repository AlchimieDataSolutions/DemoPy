# adstoolbox[pgsql]
"""
Lecture : sql_query, batchs et noms de colonnes.
"""
import os

import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
ads.set_timer(state=True)
env = ads.Env(logger=logger)

# ---------------------------------------------------------------------------
# 1. Connexion
# ---------------------------------------------------------------------------
# batch_size fixe le nombre de lignes remontées par itération du générateur.
# C'est le levier mémoire principal : 10 pour observer, 10 000 en production.
source = ads.DbPgsql(
    {
        "database": env.PG_DWH_DB,
        "user": env.PG_DWH_USER,
        "password": env.PG_DWH_PWD,
        "port": env.PG_DWH_PORT,
        "host": env.PG_DWH_HOST,
    },
    logger=logger,
    batch_size=1_000,
)
source.connect()

# ---------------------------------------------------------------------------
# 2. sql_query renvoie un GÉNÉRATEUR de batchs
# ---------------------------------------------------------------------------
# Rien n'est exécuté tant qu'on n'itère pas : c'est un générateur, pas une
# liste. Chaque élément est un batch, c'est-à-dire une liste de tuples.
generator = source.sql_query(
    query="SELECT * FROM insert_test LIMIT 5000;",
    return_columns=False,   # défaut : uniquement les données
)

row = None
for batch in generator:
    for row in batch:
        continue
print(row)

# Conséquence du générateur : on ne peut pas le parcourir deux fois, et
# len() ne fonctionne pas dessus. Pour compter sans tout charger, préférez
# sql_scalaire("SELECT COUNT(*) ...").

# ---------------------------------------------------------------------------
# 3. Récupérer les noms de colonnes : return_columns=True
# ---------------------------------------------------------------------------
# Avec return_columns=True, le PREMIER élément produit par le générateur
# n'est pas un batch de données mais la description des colonnes (le
# cursor.description du driver). Les batchs suivants sont les données.
#
# Indispensable pour un SELECT * dont on ne connaît pas le schéma à l'avance,
# ou pour construire un DataFrame avec les bons en-têtes.
generator = source.sql_query(
    query="SELECT * FROM insert_test;",
    return_columns=True,
)

description = next(generator)          # premier yield : les colonnes
noms = [col[0] for col in description]  # col[0] est le nom, les autres champs
                                        # décrivent le type selon la DB-API
logger.info(f"Colonnes : {noms}")

for batch in generator:                 # les yields suivants : les données
    for row in batch:
        continue

# Piège : ne bouclez pas directement sur le générateur avec
# return_columns=True sans consommer d'abord la description, sinon le premier
# tour de boucle traiterait les métadonnées comme une ligne de données.

# ---------------------------------------------------------------------------
# 4. Construire un DataFrame avec les bons en-têtes
# ---------------------------------------------------------------------------
# polars est déjà installé par l'extra pgsql.
import polars as pl  # noqa: E402

generator = source.sql_query(query="SELECT * FROM insert_test;", return_columns=True)
noms = [col[0] for col in next(generator)]

lignes = []
for batch in generator:
    lignes.extend(batch)

if lignes:
    df = pl.DataFrame(lignes, schema=noms, orient="row", strict=False)
    print(df.head(3))

# Pour un transfert complet vers une autre base, ne faites pas ça à la main :
# Pipeline s'en charge, avec l'inférence de types et les batchs.
# Voir pipeline/pipeline.py.

source.disconnect()