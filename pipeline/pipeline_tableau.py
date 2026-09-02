import os
from utils import data
import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
ads.set_timer(state=True)
env = ads.Env(logger)

# Instanciation d'une connexion à une base PostgreSQL, ce sera notre destination
# adstoolbox[pgsql]
source_pg = ads.DbPgsql({
    'database': env.PG_DWH_DB,
    'user': env.PG_DWH_USER,
    'password': env.PG_DWH_PWD,
    'port': env.PG_DWH_PORT,
    'host': env.PG_DWH_HOST
}, logger)

table = "insert_test"
cols = [
    'id_int', 'name_varchar', 'code_char', 'description_text', 'count_int', 'id_bigint', 'amount_numeric',
    'price_numeric', 'ratio_double', 'score_real', 'created_date', 'created_at', 'updated_at', 'event_time',
    'is_active', 'uuid_key'
]

# Déclarer une destination
destination = {
    'name': 'demo',
    'db': source_pg,
    'schema': '',
    'table': 'insert_test',
    'cols': cols
}

# Déclaration du pipeline
pipe = ads.Pipeline({
    # Pas de 'db_source'
    # Pas de 'query_source'
    'tableau': data, # Le tableau qui sert de source
    'db_destination': destination, # La destination du pipeline
    # Choix de l'opération, 'insert' par défaut
    # Choix de la méthode, 'bulk' par défaut
    # 'batch_size': 10_000 par défaut
}, logger)

print(f"Résultats : {pipe.run()}")