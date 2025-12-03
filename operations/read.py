import utils
import os
import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
ads.set_timer(state=True)
env = ads.Env(logger)

source = ads.DbPgsql({
    'database': env.PG_DWH_DB,
    'user': env.PG_DWH_USER,
    'password': env.PG_DWH_PWD,
    'port': env.PG_DWH_PORT,
    'host': env.PG_DWH_HOST
}, logger)

# Ne pas oublier de se connecter
source.connect()

# sqlQuery renvoie un generateur de batchs composés de listes de valeurs
generator = source.sql_query("SELECT * FROM insert_test;")

# Ceci est la méthode la plus simple pour parcourir ces données
for batch in generator:
    for row in batch:
        data = row