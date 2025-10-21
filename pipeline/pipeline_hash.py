import os
from uuid import uuid4
import adsToolBox as ads
from datetime import datetime, date, time

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
ads.set_timer(True)
env = ads.env(logger)

# Cette démonstration est très similaire à la première, nous montrons juste le calcul automatique du hash

# Instanciation d'une connexion à une base PostgreSQL, ce sera notre destination
source_pg = ads.dbPgsql({
    'database': env.PG_DWH_DB,
    'user': env.PG_DWH_USER,
    'password': env.PG_DWH_PWD,
    'port': env.PG_DWH_PORT,
    'host': env.PG_DWH_HOST
}, logger)

# Instanciation d'une connexion à une base MySQL, ce sera notre source
source_mysql = ads.dbMysql({
    'database': env.MYSQL_DWH_DB,
    'user': env.MYSQL_DWH_USER,
    'password': env.MYSQL_DWH_PWD,
    'port': env.MYSQL_DWH_PORT,
    'host': env.MYSQL_DWH_HOST
}, logger)

# On va donc y insérer des données
table = "insert_test"

source_mysql.connect()
source_mysql.sqlExec(f"DROP TABLE IF EXISTS {table};")
source_mysql.sqlExec(f"""
CREATE TABLE {table} (
    id_int INT, name_varchar VARCHAR(50), code_char CHAR(10), description_text TEXT, count_int INT, id_bigint BIGINT,
    amount_numeric DECIMAL(18,3), price_numeric DECIMAL(18,2), ratio_double DOUBLE, score_real REAL, created_date DATE,
    created_at DATETIME, updated_at DATETIME, event_time TIME, is_active BOOLEAN, uuid_key CHAR(36)
);""")

data = [
    [
        i, f"User{i}", f"C{i:03d}", f"Produit {i}", i*2, 1000000000000 + i, round(10.5 * i, 3), round(.5 * i, 2),
        round(1.0 + i * .1, 2), round(.5 + i * .05, 2), date(2025, 10, (i%28)+1),
        datetime(2025, 10, (i % 28)+1, 8+i%12, 0, 0),
        datetime(2025, 10, (i % 28)+1, 16, i % 60, 0),
        time(9+i%12, 30, 0), i % 2 == 0,
        str(uuid4())
    ]
    for i in range(1, 50_001)
]

cols = [
    'id_int', 'name_varchar', 'code_char', 'description_text', 'count_int', 'id_bigint', 'amount_numeric',
    'price_numeric', 'ratio_double', 'score_real', 'created_date', 'created_at', 'updated_at', 'event_time',
    'is_active', 'uuid_key'
]

# On remplit la source
print(source_mysql.insertBulk('', table, cols, data))

# Déclarer une destination
destination = {
    'name': 'demo',
    'db': source_pg,
    'schema': '',
    'table': 'insert_test',
    'cols': cols + ['hash'],
    'hash': 'hash' # Ce paramètre qui va générer le hash pour toute la ligne dans la colonne spécifiée
}

# Voici la requête pour la source (lecture des données)
query = f"""
SELECT id_int, name_varchar, code_char, description_text, count_int, id_bigint, amount_numeric,
    price_numeric, ratio_double, score_real, created_date, created_at, updated_at, 
    TIME_FORMAT(event_time, '%H:%i:%s') AS event_time, is_active, uuid_key FROM insert_test;
"""

# Déclaration du pipeline
pipe = ads.pipeline({
    'db_source': source_mysql, # La source du pipeline
    'query_source': query, # La requête qui sera exécutée sur cette source
    'db_destination': destination, # La destination du pipeline
}, logger)

# pipeline.run() renvoie les résultats du pipeline
print(f"Résultats : {pipe.run()}")

# On va requêter la table dans laquelle run a inséré
print(list(source_pg.sqlQuery(f"SELECT hash FROM {table} LIMIT 10;")))