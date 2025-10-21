import os
from uuid import uuid4
import adsToolBox as ads
from datetime import datetime, date, time

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
ads.set_timer(True)
env = ads.env(logger)

# Instanciation d'une connexion à une base PostgreSQL, ce sera notre destination
source_pg = ads.dbPgsql({
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

# Déclarons une source, mais cette fois ce sera un tableau
source = [
    (
        i, f"User{i}", f"C{i:03d}", f"Produit {i}", i*2, 1000000000000 + i, round(10.5 * i, 3), round(.5 * i, 2),
        round(1.0 + i * .1, 2), round(.5 + i * .05, 2), date(2025, 10, (i%28)+1),
        datetime(2025, 10, (i % 28)+1, 8+i%12, 0, 0),
        datetime(2025, 10, (i % 28)+1, 16, i % 60, 0),
        time(9+i%12, 30, 0), i % 2 == 0,
        str(uuid4())
    )
    for i in range(1, 50_001)
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
pipe = ads.pipeline({
    # Pas de 'db_source'
    # Pas de 'query_source'
    'tableau': source, # Le tableau qui sert de source
    'db_destination': destination, # La destination du pipeline
    # Choix de l'opération, 'insert' par défaut
    # Choix de la méthode, 'bulk' par défaut
    # 'batch_size': 10_000 par défaut
}, logger)

print(f"Résultats : {pipe.run()}")