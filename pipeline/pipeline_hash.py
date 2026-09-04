# adstoolbox[mysql,pgsql]
"""
Pipeline : empreinte de ligne automatique.

La clé 'hash' de db_destination fait calculer par le pipeline une empreinte
MD5 de chaque ligne, écrite dans une colonne dédiée. Sert à détecter les
lignes modifiées entre deux chargements sans comparer champ par champ.
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

# ---------------------------------------------------------------------------
# 1. Déclarer la colonne d'empreinte
# ---------------------------------------------------------------------------
# Trois conditions, toutes obligatoires :
#   - 'hash' nomme la colonne d'empreinte ;
#   - cette colonne doit figurer dans 'cols', SINON le calcul est
#     silencieusement désactivé (le pipeline teste `hash_col in cols`) ;
#   - cols_def doit avoir une entrée de plus, pour cette colonne.
#
# L'empreinte est un MD5 hexadécimal de 32 caractères : VARCHAR(32) suffit,
# VARCHAR(255) laisse de la marge.
cols_def = [
    "INTEGER", "VARCHAR(255)", "CHAR(100)", "TEXT", "INTEGER", "BIGINT",
    "NUMERIC(18,6)", "NUMERIC(10,2)", "DOUBLE PRECISION", "REAL", "DATE",
    "TIMESTAMP", "TIMESTAMP", "TIME", "BOOLEAN", "UUID",
    "VARCHAR(255)",   # la colonne hash, en dernier
]

destination = {
    "name": "demo",
    "db": dest_pg,
    "schema": "",
    "table": table,
    "cols": cols + ["hash"],   # la colonne d'empreinte fait partie des cols
    "hash": "hash",            # son nom
    "cols_def": cols_def,
}

query = f"""
SELECT id_int, name_varchar, code_char, description_text, count_int, id_bigint,
    amount_numeric, price_numeric, ratio_double, score_real, created_date,
    created_at, updated_at,
    TIME_FORMAT(event_time, '%H:%i:%s') AS event_time,
    is_active, uuid_key
FROM {table};
"""

# La requête source ne ramène PAS la colonne hash : elle n'existe pas côté
# source. Le pipeline l'ajoute lui-même à chaque ligne, après lecture.

pipe = ads.Pipeline(
    {
        "db_source": source_mysql,
        "query_source": query,
        "db_destination": destination,
    },
    logger=logger,
)

pipe.create_destination_table(drop=True)
print(f"Résultats : {pipe.run()}")

# ---------------------------------------------------------------------------
# 2. Ce que couvre l'empreinte
# ---------------------------------------------------------------------------
# Le hash est calculé sur TOUTES les colonnes de 'cols' SAUF la colonne
# d'empreinte elle-même, concaténées avec un séparateur '|'. Les valeurs
# nulles sont représentées par la chaîne "null".
#
# Conséquences pratiques :
#   - ajouter ou retirer une colonne de 'cols' change TOUTES les empreintes :
#     une comparaison avec un chargement antérieur devient invalide ;
#   - l'ordre des colonnes compte, puisque c'est une concaténation ;
#   - une valeur nulle et la chaîne littérale "null" donnent la même
#     empreinte. Cas rare, mais réel sur des données textuelles.
print(list(dest_pg.sql_query(query=f"SELECT hash FROM {table} LIMIT 10;")))

# ---------------------------------------------------------------------------
# 3. Usage typique : détecter les lignes modifiées
# ---------------------------------------------------------------------------
# Avec la colonne d'empreinte en place, un rechargement se compare en une
# jointure sur (clé métier, hash) au lieu de comparer chaque champ :
#
#   SELECT s.* FROM staging s
#   LEFT JOIN persistent p ON s.id_int = p.id_int
#   WHERE p.id_int IS NULL          -- lignes nouvelles
#      OR p.hash <> s.hash          -- lignes modifiées
#
# C'est exactement le principe que ChangeDataCapture industrialise, avec
# gestion de l'historique et des suppressions : voir cdc.py.

source_mysql.disconnect()
dest_pg.disconnect()