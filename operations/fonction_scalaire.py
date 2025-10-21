import os
import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
ads.set_timer(True)
env = ads.env(logger)

# la méthode sqlScalaire permet de ne renvoyer qu'une seule valeur

source = ads.dbPgsql({
    'database': env.PG_DWH_DB,
    'user': env.PG_DWH_USER,
    'password': env.PG_DWH_PWD,
    'port': env.PG_DWH_PORT,
    'host': env.PG_DWH_HOST
}, logger)

source.connect()

print(source.sqlScalaire('SELECT NOW()'))

# Attention si plusieurs champs sont demandés, sqlScalaire renvoie le premier uniquement
print(source.sqlScalaire("SELECT 1, NOW()"))