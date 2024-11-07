from CommonLib import *

logger = ads.Logger(None, ads.Logger.DEBUG, "Logger",
                    "LOGS", "LOGS_details")
logger.info("Début de la démonstration.")

# Le logger n'a pas de connexion pour ses logs
logger.set_connection(source_pg)

# Si les tables de logs n'existent pas, il faut appeler
logger.create_logs_tables()

logger.error("Message d'erreur")

logger.debug("Message de debug")

logger.warning("Message de warning")

logger.disable() # Cette commande désactive l'affichage des logs et l'insertion des logs en base
# Tous les logs ne sont pas insérés en base, seuls les opérations liés aux bdd le sont

logger.info("Toi tu ne t'afficheras pas")

logger.enable() # Par défaut, se réactive avec le niveau INFO

# Avec chaque opération sur une base ads, une ligne sera insérée dans la table LOGS_details
# Pour effectuer une insertion dans la table de logs principale, il faut appeler
logger.log_close("DEMO", "Message type")
# Attention log_close désactive les logs, logger.enable() si besoin
