import os
import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
ads.set_timer(True)
env = ads.env(logger)

# Instanciation d'une connexion à une base PostgreSQL, ce sera notre destination
source = ads.dbPgsql({
    'database': env.PG_DWH_DB,
    'user': env.PG_DWH_USER,
    'password': env.PG_DWH_PWD,
    'port': env.PG_DWH_PORT,
    'host': env.PG_DWH_HOST
}, logger)
source.connect()

# Cette ligne va chercher une ligne %User1 dans toutes les tables de tous les schémas, et logger toutes les 50
# colonnes vérifiées, le retour est une liste de dictionnaire
results = source.find_text_anywhere("User1%", include_views=False, schema=None, table=None, log_every=50)
for result in results:
    schema = result['schema'] # Le schéma dans lequel on a trouvé User1%
    table = result['table'] # La table dans laquelle on a trouvé User1%
    column = result['column'] # La colonne dans laquelle on a trouvé User1%
    count = result['count'] # Le nombre de fois où on l'a trouvé dans cette colonne
    query = result['query'] # La requête pour retrouver cette valeur

    print(f"User1% trouvé {count} fois dans {schema}.{table}.{column}, on peut le(s) retrouver avec cette requête: {query}")