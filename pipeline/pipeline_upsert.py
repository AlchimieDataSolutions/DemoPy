# adstoolbox[mysql,pgsql]
"""
Pipeline : upsert et insert_method.

Ces deux réglages n'étaient démontrés nulle part dans le dépôt : seul
l'upsert au niveau DataFactory l'était (operations/insert.py). Ici c'est le
Pipeline qui pilote l'opération.
"""
import os
import sys
from pathlib import Path

import adsToolBox as ads

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import utils  # noqa: E402

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
ads.set_timer(state=True)
env = ads.Env(logger=logger)

dest_pg = ads.DbPgsql(
    {
        "database": env.PG_DWH_DB,
        "user": env.PG_DWH_USER,
        "password": env.PG_DWH_PWD,
        "port": env.PG_DWH_PORT,
        "host": env.PG_DWH_HOST,
    },
    logger=logger,
)
dest_pg.connect()

table = "upsert_test"
cols = ["id_int", "name_varchar", "count_int"]
cols_def = ["INTEGER PRIMARY KEY", "VARCHAR(50)", "INTEGER"]

# ---------------------------------------------------------------------------
# 1. La table cible doit avoir une contrainte d'unicité
# ---------------------------------------------------------------------------
# L'upsert PostgreSQL repose sur ON CONFLICT, qui exige un index unique ou
# une clé primaire sur les colonnes de conflit. Sans cette contrainte, la
# requête échoue côté serveur — le pipeline consignera le rejet sans
# expliquer que le problème est le schéma cible.
dest_pg.sql_exec(query=f"DROP TABLE IF EXISTS {table};")
dest_pg.sql_exec(query=f"""
CREATE TABLE {table} (
    id_int INTEGER PRIMARY KEY,
    name_varchar VARCHAR(50),
    count_int INTEGER
);""")

# ---------------------------------------------------------------------------
# 2. Premier passage : insertion
# ---------------------------------------------------------------------------
lignes_initiales = [[i, f"User{i}", i] for i in range(1, 101)]

destination = {
    "name": "demo_upsert",
    "db": dest_pg,
    "schema": "",
    "table": table,
    "cols": cols,
    "cols_def": cols_def,
    # conflict_cols : les colonnes sur lesquelles Pipeline détecte le conflit.
    # C'est l'équivalent du ON CONFLICT (...) de PostgreSQL. Obligatoire dès
    # que operation_type vaut 'upsert' : sans elles, la requête générée est
    # invalide.
    "conflict_cols": ["id_int"],
}

pipe = ads.Pipeline(
    {
        "tableau": lignes_initiales,
        "db_destination": destination,
        "operation_type": "insert",
        "insert_method": "bulk",
        "batch_size": 50,
    },
    logger=logger,
)
print(f"Insertion initiale : {pipe.run()}")

# ---------------------------------------------------------------------------
# 3. Second passage : upsert
# ---------------------------------------------------------------------------
# Les 50 premières lignes existent déjà avec des valeurs différentes, les 50
# suivantes sont nouvelles. Un 'insert' violerait la clé primaire ; l'upsert
# met à jour les unes et insère les autres.
lignes_modifiees = [[i, f"Modifie{i}", i * 100] for i in range(51, 151)]

pipe_upsert = ads.Pipeline(
    {
        "tableau": lignes_modifiees,
        "db_destination": destination,
        "operation_type": "upsert",     # <- le réglage démontré ici
        "insert_method": "bulk",
        "batch_size": 50,
    },
    logger=logger,
)
print(f"Upsert : {pipe_upsert.run()}")

# Vérification : 150 lignes, dont 100 modifiées.
total = dest_pg.sql_scalaire(query=f"SELECT COUNT(*) FROM {table}")
modifiees = dest_pg.sql_scalaire(
    query=f"SELECT COUNT(*) FROM {table} WHERE name_varchar LIKE 'Modifie%'",
)
logger.info(message=f"{total} ligne(s) au total, dont {modifiees} modifiée(s)")

# ---------------------------------------------------------------------------
# 4. insert_method : bulk ou executemany
# ---------------------------------------------------------------------------
# 'bulk' (défaut) passe par le chargement en masse natif du SGBD — COPY sur
# PostgreSQL, BULK INSERT sur SQL Server. C'est nettement plus rapide, et
# c'est ce qu'il faut sur de gros volumes.
#
# Pour l'upsert, bulk crée en plus une table temporaire intermédiaire, puis
# fait un MERGE depuis celle-ci.
#
# 'executemany' envoie les lignes par lots via le driver. Plus lent, mais
# utile quand le chargement en masse est refusé : droits insuffisants,
# base distante bridée, ou table avec des déclencheurs que COPY contourne.
pipe_many = ads.Pipeline(
    {
        "tableau": [[i, f"Many{i}", i] for i in range(151, 201)],
        "db_destination": destination,
        "operation_type": "upsert",
        "insert_method": "executemany",   # <- l'autre méthode
        "batch_size": 25,
    },
    logger=logger,
)
print(f"Upsert executemany : {pipe_many.run()}")

# Une valeur inconnue d'operation_type ou d'insert_method lève un
# NotImplementedError explicite, propagé par run() — contrairement aux
# erreurs d'insertion, qui sont seulement consignées.
try:
    ads.Pipeline(
        {
            "tableau": [[999, "X", 1]],
            "db_destination": destination,
            "operation_type": "merge",   # n'existe pas
        },
        logger=logger,
    ).run()
except NotImplementedError as e:
    logger.info(message=f"Opération inconnue, exception attendue : {e}")

dest_pg.disconnect()