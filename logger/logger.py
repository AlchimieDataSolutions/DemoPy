from util import *

logger = ads.Logger(None, logging.DEBUG, "Logger")
logger.info("Début de la démonstration.")

logger.error("Message d'erreur")

logger.debug("Message de debug")

logger.warning("Message de warning")

logger.disable() # Cette commande désactive l'affichage des logs et l'insertion des logs en base
# Tous les logs ne sont pas insérés en base, seuls les opérations liés aux bdd le sont

logger.info("Toi tu ne t'afficheras pas")

logger.enable() # Par défaut, se réactive avec le niveau INFO
logger.info("Fin de la démonstration !")
