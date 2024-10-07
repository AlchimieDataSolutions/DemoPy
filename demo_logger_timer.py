import adsGenericFunctions as ads
from env import *
import logging
import psycopg2

# Établit une connexion pour que le logger puisse écrire en base
logger_connection = psycopg2.connect(database=pg_dwh_db, user=pg_dwh_user, password=pg_dwh_pwd, port=pg_dwh_port,
                                     host=pg_dwh_host)
logger = ads.Logger(logger_connection, logging.INFO, "AdsLogger", "LOGS", "LOGS_details")
logger.info("Début de la démonstration.")

# Active le timer, les requêtes seront chronométrées, si le logger n'est pas activé, les temps d'exécutions ne seront pas affichés
ads.set_timer(True)

# On définit une source de connexion à laquelle on affecte notre logger
source = ads.dbPgsql({'database': pg_dwh_db
                          , 'user': pg_dwh_user
                          , 'password': pg_dwh_pwd
                          , 'port': pg_dwh_port
                          , 'host': pg_dwh_host},
                      logger)

# Cette opération sera loguée et chronométrée
source.connect()

# Celle-ci le sera dès que le flux (générateur) renvoyé par sqlQuery sera consommé
data1 = source.sqlQuery('''SELECT tenantname, fichier FROM onyx_qs."diskcheck" LIMIT 10''')
print(f"First read: {list(data1)}")
# Après ce print viennent les notifications d'insertions des logs en base et le temps d'eéxuction

# Voici comment désactiver les logs
logger.disable_logging()
logger.info("Ceci est un message d'information qui n'est pas censé s'afficher.")

data2 = source.sqlQuery('''SELECT tenantname, fichier FROM onyx_qs."diskcheck" LIMIT 10''')
print(f"Second read: {list(data2)}")
# Ici pas d'insertions en base de logs non plus, et pas de temps d'exécutions affiché

logger.enable_logging()
logger.info("Fin de la démonstration !")
