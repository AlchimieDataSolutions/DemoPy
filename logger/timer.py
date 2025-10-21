import os
import datetime
import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
env = ads.env(logger)

# Active le timer, si le logger n'est pas activé, les temps d'exécutions ne seront pas affichés
ads.set_timer(True)

# La plupart des fonctions d'adsToolBox sont chronométrés par défaut
# Instanciation d'une connexion à une base PostgreSQL
source = ads.dbPgsql({'database':env.PG_DWH_DB
                    , 'user':env.PG_DWH_USER
                    , 'password':env.PG_DWH_PWD
                    , 'port':env.PG_DWH_PORT
                    , 'host':env.PG_DWH_HOST}, logger, 10)
source.connect()

# On peut aussi affecter le décorateur timer à n'importe quelle méthode
@ads.timer
def sample_function(duration, logger=None):
    """ Une fonction d'exemple qui simule une tâche en attendant un certain temps. """
    import time
    time.sleep(duration)
    return "Done"

# Par contre, il faut absolument un argument 'logger' dans les paramètres de la fonction en question
sample_function(0.1, logger=logger)

# On peut aussi changer de fuseau horaire pendant tout un traitement
print(f"Heure locale avant set_timzeone: {datetime.datetime.now()}")

ads.set_timezone('America/New_York')

# Si l'OS est Windows, il faudra appeler ads.now(), si c'est Unix, datetime fonctionnera aussi
print(f"Heure après set_timezone: {ads.now()}")