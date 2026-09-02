import utils
import os
import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
ads.set_timer(state=True)
env = ads.Env(logger)

# La méthode sql_scalaire permet de ne renvoyer qu'une seule valeur

# adstoolbox[pgsql]
source = ads.DbPgsql({
    'database': env.PG_DWH_DB,
    'user': env.PG_DWH_USER,
    'password': env.PG_DWH_PWD,
    'port': env.PG_DWH_PORT,
    'host': env.PG_DWH_HOST
}, logger)

source.connect()

print(source.sql_scalaire('SELECT NOW()'))
print(source.sql_scalaire('SELECT COUNT(*) FROM insert_test;'))

# Attention si plusieurs champs sont demandés, sql_scalaire renvoie le premier uniquement
print(source.sql_scalaire("SELECT 1, NOW()"))