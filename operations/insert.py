import os
from uuid import uuid4
import adsToolBox as ads
from datetime import datetime, date, time

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
ads.set_timer(True)
env = ads.env(logger)

source = ads.dbPgsql({
    'database': env.PG_DWH_DB,
    'user': env.PG_DWH_USER,
    'password': env.PG_DWH_PWD,
    'port': env.PG_DWH_PORT,
    'host': env.PG_DWH_HOST
}, logger)

# Ne pas oublier de se connecter
source.connect()

source.sqlExec("TRUNCATE TABLE insert_test;")
cols = [
    'id_int', 'name_varchar', 'code_char', 'description_text', 'count_int', 'id_bigint', 'amount_numeric',
    'price_numeric', 'ratio_double', 'score_real', 'created_date', 'created_at', 'updated_at', 'event_time',
    'is_active', 'uuid_key'
]
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

# Différentes méthode d'insertion existent

# Celle-ci n'insère qu'une seule ligne
source.insert('', 'insert_test', cols, data[0])

# Celle-ci insère des batch via executemany
source.insertMany('', 'insert_test', cols, data[1:1_000])

# Celle-ci insère des batch via une insertion en bulk bien plus rapide
source.insertBulk('', 'insert_test', cols, data[1_001:])

# Une autre opération existe: upsert
# On aura besoin de conflict_cols qui répertorie les PK sur lesquels la comparaison sera faite pour savoir si on
# insère ou si on met à jour

source.sqlExec("""
ALTER TABLE insert_test DROP CONSTRAINT IF EXISTS unique_id_name;
ALTER TABLE insert_test ADD CONSTRAINT unique_id_name UNIQUE (id_int, name_varchar);""")
source.upsert('', 'insert_test', cols, data[0], cols[:2])

# De la même façon, on a un upsertMany et un upsertBulk (cette dernière crée une table temporaire)
source.upsertMany('', 'insert_test', cols, data[1:1_000], cols[:2])

source.upsertBulk('', 'insert_test', cols, data[1_001:], cols[:2])