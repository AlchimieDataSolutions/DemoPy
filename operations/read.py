import os
import adsToolBox as ads

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

# sqlQuery renvoie un generateur
generator = source.sqlQuery("SELECT * FROM insert_test;")

# Ceci est la méthode pour parcourir ces données
for batch in generator:
    for row in batch:
        data = row