from CommonLib import *

# Active le timer, les requêtes seront chronométrées, si le logger n'est pas activé, les temps d'exécutions ne seront
# pas affichés
ads.set_timer(True)

# Toutes les fonctions d'adsToolBox sont chronométrés par défaut

# On peut aussi affecter le décorateur timer à n'importe quelle méthode
@ads.timer
def sample_function(duration, logger=None):
    """ Une fonction d'exemple qui simule une tâche en attendant un certain temps. """
    time.sleep(duration)
    return "Done"

# Par contre, il faut absolument un argument 'logger' dans la fonction en question
logger.enable()
sample_function(0.1, logger=logger)

logger.info("Fin de la démonstration !")

