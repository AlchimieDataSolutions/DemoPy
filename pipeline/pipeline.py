from utils import data
import os
import adsToolBox as ads

script_name = os.path.basename(__file__)
# Beaucoup de logs ici
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
ads.set_timer(state=True)
env = ads.Env(logger)

# Instanciation d'une connexion à une base PostgreSQL, ce sera notre destination
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
source_mysql.connect()

# On va donc y insérer des données
table = "insert_test"
cols = [
    'id_int', 'name_varchar', 'code_char', 'description_text', 'count_int', 'id_bigint', 'amount_numeric',
    'price_numeric', 'ratio_double', 'score_real', 'created_date', 'created_at', 'updated_at', 'event_time',
    'is_active', 'uuid_key'
]

# Voici la requête pour la source (lecture des données)
# Attention MySQL, les types TIME sont sous la forme xxh yym ce qui n'est pas lisible par défaut
# Attention SQL Server, les types UNIQUEIDENTIFIER doivent être castés en NVARCHAR(36) pour être lisible
query = f"""
SELECT id_int, name_varchar, code_char, description_text, count_int, id_bigint, amount_numeric,
    price_numeric, ratio_double, score_real, created_date, created_at, updated_at, 
    TIME_FORMAT(event_time, '%H:%i:%s') AS event_time, is_active, uuid_key FROM insert_test;
"""

# Déclarer une destination
destination = {
    'name': 'demo',
    'db': source_pg,
    'schema': '',
    'table': 'insert_test',
    'cols': cols,
}

# Déclaration du pipeline
pipe = ads.Pipeline({
    'db_source': source_mysql, # La source du pipeline
    'query_source': query, # La requête qui sera exécutée sur cette source
    'db_destination': destination, # La destination du pipeline
    'operation_type': 'insert', # Choix de l'opération, 'insert' or 'upsert'
    'insert_method': 'bulk', # Choix de la méthode, 'bulk' or 'executemany'
    'batch_size': 10_000, # Optionnel, 10 000 par défaut
# attention le batch_size du pipeline redéfinit ceux des objets db_source et db_destination
}, logger)

# On remplit la table source
source_mysql.sql_exec(f"DROP TABLE IF EXISTS {table};")
source_mysql.sql_exec(f"""
CREATE TABLE {table} (
    id_int INT, name_varchar VARCHAR(50), code_char CHAR(10), description_text TEXT, count_int INT, id_bigint BIGINT,
    amount_numeric DECIMAL(18,3), price_numeric DECIMAL(18,2), ratio_double DOUBLE, score_real REAL, created_date DATE,
    created_at DATETIME, updated_at DATETIME, event_time TIME, is_active BOOLEAN, uuid_key CHAR(36)
);""")
print(source_mysql.insert_bulk('', table, cols, data))

# On crée la table destination
source_pg.connect()
source_pg.sql_exec(f"DROP TABLE IF EXISTS {table};")
source_pg.sql_exec(f"""
CREATE TABLE {table} (
    id_int INTEGER, name_varchar VARCHAR(255), code_char CHAR(100), description_text TEXT, count_int INTEGER, 
    id_bigint BIGINT, amount_numeric NUMERIC(18,6), price_numeric NUMERIC(10,2), ratio_double DOUBLE PRECISION, 
    score_real REAL, created_date DATE, created_at TIMESTAMP, updated_at TIMESTAMP, event_time TIME, is_active BOOLEAN, 
    uuid_key UUID
);""")

# pipeline.run() renvoie les résultats du pipeline
print(f"Résultats : {pipe.run()}")

# Dans cette configuration, Polars va essayer de déterminer lui-même les types des données, pour qu'il évite de le
# faire sur chaque batch, il va garder le même schéma au long du run, si le premier batch n'a pas suffi a déterminer
# le type d'une colonne, une réinférence partielle sera effectuée sur le batch suivant jusqu'à avoir un schéma complet