import utils
import os
import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
ads.set_timer(state=True)
env = ads.Env(logger)

# la méthode sql_exec permet d'exécuter des requêtes diverses sur la base sans vouloir de retour
# adstoolbox[pgsql]
source = ads.DbPgsql({
    'database': env.PG_DWH_DB,
    'user': env.PG_DWH_USER,
    'password': env.PG_DWH_PWD,
    'port': env.PG_DWH_PORT,
    'host': env.PG_DWH_HOST
}, logger)

source.connect()
source.sql_exec("DROP TABLE IF EXISTS demo_insert;")
source.sql_exec('''
CREATE TABLE IF NOT EXISTS demo_insert (
    id SERIAL PRIMARY KEY,
    tenantname VARCHAR(255),
    fichier VARCHAR(255)
);''')