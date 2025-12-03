import os
from utils import data
import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
ads.set_timer(state=True)
env = ads.Env(logger)

# Polars va automatiquement chercher à inférer sur les données pour définir leur type
# mais c'est quelque chose qu'on peut éviter
source_pg = ads.DbPgsql({
    'database': env.PG_DWH_DB,
    'user': env.PG_DWH_USER,
    'password': env.PG_DWH_PWD,
    'port': env.PG_DWH_PORT,
    'host': env.PG_DWH_HOST
}, logger)

# Instanciation d'une connexion à une base MySQL, ce sera notre source
source_mysql = ads.DbMysql({
    'database': env.MYSQL_DWH_DB,
    'user': env.MYSQL_DWH_USER,
    'password': env.MYSQL_DWH_PWD,
    'port': env.MYSQL_DWH_PORT,
    'host': env.MYSQL_DWH_HOST
}, logger)

table = "insert_test"

source_mysql.connect()
source_mysql.sql_exec(f"DROP TABLE IF EXISTS {table};")
source_mysql.sql_exec(f"""
CREATE TABLE {table} (
    id_int INT, name_varchar VARCHAR(50), code_char CHAR(10), description_text TEXT, count_int INT, id_bigint BIGINT,
    amount_numeric DECIMAL(18,3), price_numeric DECIMAL(18,2), ratio_double DOUBLE, score_real REAL, created_date DATE,
    created_at DATETIME, updated_at DATETIME, event_time TIME, is_active BOOLEAN, uuid_key CHAR(36)
);""")

cols = [
    'id_int', 'name_varchar', 'code_char', 'description_text', 'count_int', 'id_bigint', 'amount_numeric',
    'price_numeric', 'ratio_double', 'score_real', 'created_date', 'created_at', 'updated_at', 'event_time',
    'is_active', 'uuid_key'
]

# On remplit la source
print(source_mysql.insert_bulk('', table, cols, data))

# Il faut définir les types des colonnes de la destination
cols_def = [
    'INTEGER', 'VARCHAR(255)', 'CHAR(100)', 'TEXT', 'INTEGER', 'BIGINT', 'NUMERIC(18,6)', 'NUMERIC(10,2)',
    'DOUBLE PRECISION', 'REAL', 'DATE', 'TIMESTAMP', 'TIMESTAMP', 'TIME', 'BOOLEAN', 'UUID'
]

# Déclarer une destination
destination = {
    'name': 'demo',
    'db': source_pg,
    'schema': '',
    'table': 'insert_test',
    'cols': cols,
    'cols_def': cols_def # C'est l'attribut important
}

# Voici la requête pour la source (lecture des données)
query = f"""
SELECT id_int, name_varchar, code_char, description_text, count_int, id_bigint, amount_numeric,
    price_numeric, ratio_double, score_real, created_date, created_at, updated_at, 
    TIME_FORMAT(event_time, '%H:%i:%s') AS event_time, is_active, uuid_key FROM insert_test;
"""

# Déclaration du pipeline
pipe = ads.Pipeline({
    'db_source': source_mysql, # La source du pipeline
    'query_source': query, # La requête qui sera exécutée sur cette source
    'db_destination': destination, # La destination du pipeline
}, logger)

# Cette méthode s'occupe de créer la table de destination, si drop est à True, la table sera supprimée avant
pipe.create_destination_table(drop=True)

# Cette fois-ci, Polars ne va pas essayer d'inférer sur les données mais va utiliser cols_def pour son schéma
# ce qui est un gros gain de performances
print(pipe.run())