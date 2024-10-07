from get_api_data import *
import adsGenericFunctions as ads
from env import *
import psycopg2
import logging


logger_connection = psycopg2.connect(database=pg_dwh_db, user=pg_dwh_user, password=pg_dwh_pwd, port=pg_dwh_port,
                                     host=pg_dwh_host)
logger = ads.Logger(logger_connection, logging.INFO, "AdsLogger", "LOGS", "LOGS_details")
logger.info("Début de la démonstration...")
logger.disable_logging()

# On active le timer, les requêtes seront chronométrées
ads.set_timer(True)

monAPI=NxOnyxApi(domain=ORISHA_PROD_TENANTDOMAIN,username=ORISHA_PROD_TENANTUSERNAME,password=ORISHA_PROD_TENANTPASSWORD,tenantId=ORISHA_PROD_TENANTID)
data=monAPI.getTree()


# Extraire la liste des clés
noms_cles = list(data[0].keys())  # on prend les clés du premier dictionnaire

# Extraire la liste des valeurs sous forme de tuples
valeurs_tuples = [tuple(d.values()) for d in data]

print("Noms des clés :", noms_cles)
print("Valeurs sous forme de tuples :", valeurs_tuples)

destination = ads.dbPgsql({'database':pg_dwh_db
                    , 'user':pg_dwh_user
                    , 'password':pg_dwh_pwd
                    , 'port':pg_dwh_port
                    , 'host':pg_dwh_host}, logger)

pipeline = ads.pipelineTableau({'tableau': valeurs_tuples, 'db_destination': destination, 'table': 'onyx_qs.test',
                 'cols': noms_cles}, logger)

pipeline.run()
logger.info("Fin de la démonstration")