from CommonLib import *

logger = ads.Logger(ads.Logger.DEBUG, "Logger","LOGS", "LOGS_details")
logger.info("Début de la démonstration.")

logger.set_connection(source_pg, ads.Logger.DEBUG) #Tous les logs au >= DEBUG seront insérés dans LOGS_details

# Si les tables de logs n'existent pas, il faut appeler
logger.create_logs_tables()

logger.debug("Message de debug")
logger.info("Message d'info")
logger.warning("Message de warning")
logger.error("Message d'erreur")
logger.custom_log(25, "Message avec niveau custom")

logger.disable() # Cette commande désactive l'affichage des logs et l'insertion des logs en base

logger.info("Toi tu ne t'afficheras pas")

logger.enable() # Par défaut, se réactive avec le niveau INFO

logger.info("Mais toi oui")

# Avec chaque opération sur une base ads, une ligne sera insérée dans la table LOGS_details
# Pour effectuer une insertion dans la table de logs principale, il faut appeler
logger.log_close("DEMO", "Message type")
# Attention log_close désactive les logs, logger.enable() si besoin
