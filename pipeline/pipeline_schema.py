# adstoolbox[mysql,pgsql]
"""
Pipeline : typage explicite plutôt qu'inféré.

Anciennement polars_inference.py. Renommé parce que le sujet n'est pas
l'inférence de Polars mais la clé cols_def du pipeline, et le gain à la
fournir.
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

source_mysql = ads.DbMysql(
    {
        "database": env.MYSQL_DWH_DB,
        "user": env.MYSQL_DWH_USER,
        "password": env.MYSQL_DWH_PWD,
        "port": env.MYSQL_DWH_PORT,
        "host": env.MYSQL_DWH_HOST,
    },
    logger=logger,
)
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

table = "insert_test"
cols = [
    "id_int", "name_varchar", "code_char", "description_text", "count_int",
    "id_bigint", "amount_numeric", "price_numeric", "ratio_double",
    "score_real", "created_date", "created_at", "updated_at", "event_time",
    "is_active", "uuid_key",
]

# Les types SQL de la DESTINATION, dans le même ordre que cols. C'est la clé
# du script : sans elle, Polars devine ; avec elle, il applique.
cols_def = [
    "INTEGER", "VARCHAR(255)", "CHAR(100)", "TEXT", "INTEGER", "BIGINT",
    "NUMERIC(18,6)", "NUMERIC(10,2)", "DOUBLE PRECISION", "REAL", "DATE",
    "TIMESTAMP", "TIMESTAMP", "TIME", "INTEGER", "UUID",
]

source_mysql.connect()
source_mysql.sql_exec(query=f"DROP TABLE IF EXISTS {table};")
source_mysql.sql_exec(query=f"""
CREATE TABLE {table} (
    id_int INT, name_varchar VARCHAR(50), code_char CHAR(10), description_text TEXT,
    count_int INT, id_bigint BIGINT, amount_numeric DECIMAL(18,3),
    price_numeric DECIMAL(18,2), ratio_double DOUBLE, score_real REAL,
    created_date DATE, created_at DATETIME, updated_at DATETIME, event_time TIME,
    is_active BOOLEAN, uuid_key CHAR(36)
);""")
print(source_mysql.insert_bulk(schema="", table=table, cols=cols, rows=utils.data))

query = f"""
SELECT id_int, name_varchar, code_char, description_text, count_int, id_bigint,
    amount_numeric, price_numeric, ratio_double, score_real, created_date,
    created_at, updated_at,
    TIME_FORMAT(event_time, '%H:%i:%s') AS event_time,
    is_active, uuid_key
FROM {table};
"""

destination = {
    "name": "demo",
    "db": dest_pg,
    "schema": "",
    "table": table,
    "cols": cols,
    "cols_def": cols_def,   # <- l'attribut important
}

pipe = ads.Pipeline(
    {
        "db_source": source_mysql,
        "query_source": query,
        "db_destination": destination,
    },
    logger=logger,
)

# ---------------------------------------------------------------------------
# 1. create_destination_table : créer la cible depuis cols + cols_def
# ---------------------------------------------------------------------------
# La méthode assemble le CREATE TABLE à partir des deux listes. Elle n'est
# donc utilisable QUE si cols_def est fourni.
#
# drop=True supprime la table avant de la recréer : destructeur, à réserver
# aux rechargements complets. drop=False (défaut) laisse une table existante
# en place — le message "La table de destination existe déjà" est alors un
# warning, pas une erreur.
pipe.create_destination_table(drop=True)

# Contrôle de cohérence intégré : si len(cols) != len(cols_def), un
# ValueError explicite est levé, avec les deux longueurs. C'est le seul
# endroit du pipeline où cet écart est détecté tôt.

# ---------------------------------------------------------------------------
# 2. Traduire les types SQL en types Polars
# ---------------------------------------------------------------------------
# sql_defs_to_polars_schema fait la conversion utilisée en interne par
# run(). L'appeler directement sert à VÉRIFIER la correspondance avant de
# lancer un transfert de plusieurs millions de lignes.
schema = pipe.sql_defs_to_polars_schema(cols=cols, cols_def=cols_def)
for nom, dtype in schema.items():
    logger.info(message=f"  {nom:20s} -> {dtype}")

# Deux comportements à connaître.
#
# a) Un type SQL non reconnu ne provoque PAS d'erreur : il retombe sur Utf8
#    avec un log en DEBUG ("Type SQL non reconnu ... fallback en Utf8").
#    Une faute de frappe dans cols_def donne donc une colonne texte au lieu
#    d'un entier, silencieusement pour qui ne lit pas les logs DEBUG.
schema_faute = pipe.sql_defs_to_polars_schema(
    cols=["montant"],
    cols_def=["NUMERICC(18,2)"],   # faute volontaire
)
logger.warning(message=f"Type mal orthographié -> {schema_faute}")

# b) Seule la partie avant la parenthèse est lue : VARCHAR(255) et
#    VARCHAR(10) donnent le même pl.Utf8. Les longueurs ne servent qu'au
#    CREATE TABLE, pas au typage Polars.
logger.info(message=str(pipe.sql_defs_to_polars_schema(
    cols=["a", "b"], cols_def=["VARCHAR(255)", "VARCHAR(10)"],
)))

# c) Si cols et cols_def n'ont PAS la même longueur, l'erreur est
#    déroutante : "ValueError: zip() argument 2 is shorter than argument 1",
#    sans mention de cols ni de cols_def. Pire, dans run() cette exception
#    est attrapée par la gestion de batch et devient "Échec de la création
#    du dataframe" sur CHAQUE batch, donc toutes les lignes rejetées.
#    create_destination_table(), lui, contrôle les longueurs et lève un
#    message clair : appelez-le d'abord, même avec drop=False, pour valider
#    la cohérence avant le transfert.
#
# d) Cas particulier MySQL : une colonne TIME issue d'une source MySQL est
#    forcée en Utf8, quel que soit cols_def, parce que le format renvoyé par
#    le driver n'est pas convertible en pl.Time. C'est le pendant du
#    TIME_FORMAT de la requête.

# ---------------------------------------------------------------------------
# 3. Exécution
# ---------------------------------------------------------------------------
# Avec cols_def, Polars n'infère plus : il applique le schéma dès le premier
# batch. Gain de temps sur les gros volumes, et surtout typage DÉTERMINISTE
# — l'inférence peut varier selon le contenu du premier batch.
print(pipe.run())

# Sans cols_def, le comportement est celui de pipeline.py : inférence sur le
# premier batch, réinférence partielle des colonnes restées pl.Null sur les
# batchs suivants. Une colonne entièrement nulle sur TOUT le run reste
# pl.Null, un type qui ne correspond à aucune colonne SQL et fera échouer
# l'insertion. Fournir cols_def est la seule protection contre ce cas.

source_mysql.disconnect()
dest_pg.disconnect()