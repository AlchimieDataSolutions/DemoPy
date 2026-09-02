import utils
import os
import time
from datetime import datetime
import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
env = ads.Env(logger)

# Active le timer, si le logger n'est pas activé, les temps d'exécutions ne seront pas affichés
ads.set_timer(state=True)

# La plupart des fonctions d'adsToolBox sont chronométrés par défaut
# Instanciation d'une connexion à une base PostgreSQL
# adstoolbox[pgsql]
source = ads.DbPgsql({'database':env.PG_DWH_DB
                    , 'user':env.PG_DWH_USER
                    , 'password':env.PG_DWH_PWD
                    , 'port':env.PG_DWH_PORT
                    , 'host':env.PG_DWH_HOST}, logger, 10)
source.connect()

# On peut aussi affecter le décorateur timer à n'importe quelle méthode
@ads.timer
def sample_function(duration, logger=None):
    """Une fonction d'exemple qui simule une tâche en attendant un certain temps."""
    logger.info("Cette méthode sera chronométrée.")
    time.sleep(duration)
    return None

# Sinon le logger peut être un attribut d'un objet pour que le décorateur le retrouve
class Sample:
    """Classe présente pour illustrer le fonctionnement du logger."""
    def __init__(self, logger: ads.Logger):
        self.logger = logger

    @ads.timer
    def sample_class_method(self, duration: float):
        """Une fonction d'exemple qui simule une tâche en attendant un certain temps."""
        self.logger.info("Cette méthode de classe le sera aussi.")
        time.sleep(duration)
        return None

# Il faut donc soit un argument logger dans les paramètres de la fonction, soit un logger dans les attributs de sa classe
sample_function(.1, logger=logger)
s = Sample(logger)
s.sample_class_method(.1)

# On peut aussi changer de fuseau horaire pendant tout un traitement
print(f"Heure locale avant set_timzeone: {datetime.now()}")

ads.set_timezone('America/New_York')

# Si l'OS est Windows, il faudra appeler ads.now(), si c'est Unix, datetime fonctionnera aussi
print(f"Heure après set_timezone: {ads.now()}")