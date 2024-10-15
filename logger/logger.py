import adsToolBox as ads

from env import *
import logging

# Établit une connexion pour que le logger puisse écrire en base
logger_connection = ads.dbPgsql({'database': pg_dwh_db,
                                 'user': pg_dwh_user,
                                 'password': pg_dwh_pwd,
                                 'port': pg_dwh_port,
                                 'host': pg_dwh_host}, None)
# Ne pas oublier de lancer la connection
logger_connection.connect()

logger = ads.Logger(logger_connection, logging.INFO, "AdsLogger", "LOGS", "LOGS_details")
logger.info("Début de la démonstration.")

logger.error("Message d'erreur")

logger.debug("Message de debug")

logger.warning("Message de warning")

logger.info("Fin de la démonstration !")
