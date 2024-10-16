from util import *

logger = ads.Logger(None, logging.DEBUG, "EnvLogger")
logger.info("Démo")

# Établit une pipeline pour que le logger puisse écrire en base
logger_connection = ads.dbPgsql({'database': env.PG_DWH_DB,
                                 'user': env.PG_DWH_USER,
                                 'password': env.PG_DWH_PWD,
                                 'port': env.PG_DWH_PORT,
                                 'host': env.PG_DWH_HOST}, None)
# Ne pas oublier de lancer la connection
logger_connection.connect()

logger = ads.Logger(logger_connection, logging.INFO, "AdsLogger", "LOGS", "LOGS_details")
logger.info("Début de la démonstration.")

logger.error("Message d'erreur")

logger.debug("Message de debug")

logger.warning("Message de warning")

logger.info("Fin de la démonstration !")
