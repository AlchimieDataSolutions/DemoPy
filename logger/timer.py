# adstoolbox[pgsql]
"""
Chronométrage et fuseau horaire : timer, set_timer, get_timer, now.

Seule la section 2 demande l'extra pgsql. Tout le reste tourne sur le cœur.
"""
import os
import time
from datetime import datetime

import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
env = ads.Env(logger=logger)

# ---------------------------------------------------------------------------
# 1. set_timer et get_timer : un interrupteur global
# ---------------------------------------------------------------------------
# set_timer agit sur tout le PROCESSUS, pas sur un objet. Sans lui, aucune
# durée n'est journalisée, y compris par les méthodes de la toolbox déjà
# décorées.
ads.set_timer(state=True)

# get_timer() lit cet état, ce qui permet de conditionner du code sans
# dupliquer le réglage.
print(f"Chronomètre actif ? {ads.get_timer()}")

# ---------------------------------------------------------------------------
# 2. Les méthodes de la toolbox sont déjà chronométrées
# ---------------------------------------------------------------------------
# La plupart portent @timer en interne : connect, sql_query, insert_bulk,
# transfer_file, run... Il suffit d'activer le chronomètre pour voir leurs
# durées apparaître dans les logs.
source = ads.DbPgsql(
    {
        "database": env.PG_DWH_DB,
        "user": env.PG_DWH_USER,
        "password": env.PG_DWH_PWD,
        "port": env.PG_DWH_PORT,
        "host": env.PG_DWH_HOST,
    },
    logger=logger,
    batch_size=10,
)
source.connect()

# ---------------------------------------------------------------------------
# 3. Décorer ses propres fonctions
# ---------------------------------------------------------------------------
# Le décorateur doit trouver un logger. Deux possibilités seulement :
# un argument NOMMÉ `logger`, ou un attribut `self.logger`.

@ads.timer
def sample_function(duration: float, logger: ads.Logger = None) -> None:
    """Simule une tâche en attendant un certain temps."""
    logger.info(message="Cette méthode sera chronométrée.")
    time.sleep(duration)


class Sample:
    """Illustre la découverte du logger via les attributs de la classe."""

    def __init__(self, logger: ads.Logger) -> None:
        """Stocke le logger là où le décorateur ira le chercher."""
        self.logger = logger

    @ads.timer
    def sample_class_method(self, duration: float) -> None:
        """Simule une tâche en attendant un certain temps."""
        self.logger.info(message="Cette méthode de classe le sera aussi.")
        time.sleep(duration)


sample_function(.1, logger=logger)
Sample(logger).sample_class_method(.1)

# Passer le logger en POSITIONNEL ne marche pas : le décorateur inspecte
# kwargs.get("logger"), puis args[0].logger. Un logger en deuxième position
# reste invisible.
#
#   sample_function(.1, logger)   ->  ValueError: Pas de logger défini.

# ---------------------------------------------------------------------------
# 4. Sans logger : erreur, mais seulement si le chronomètre est actif
# ---------------------------------------------------------------------------
@ads.timer
def sans_logger() -> str:
    """Fonction décorée qui n'expose aucun logger."""
    return "terminé"


try:
    sans_logger()
except ValueError as e:
    logger.info(message=f"Chronomètre actif et pas de logger -> {e}")

# Chronomètre désactivé, la même fonction s'exécute normalement : le
# décorateur consulte get_timer() à CHAQUE appel, pas à la déclaration.
ads.set_timer(state=False)
logger.info(message=f"Sans chronomètre : {sans_logger()}")

# Conséquence pratique : un @ads.timer posé sur une fonction sans logger est
# une bombe à retardement. Le code passe en développement, chronomètre
# éteint, et échoue en production dès que quelqu'un l'active.

ads.set_timer(state=True)

# ---------------------------------------------------------------------------
# 5. Combiner avec retry_on_failure
# ---------------------------------------------------------------------------
# L'ordre des décorateurs détermine ce qui est mesuré :
#
#   @ads.timer                     mesure l'ENSEMBLE des tentatives,
#   @ads.retry_on_failure()        délais d'attente compris
#   def methode(self): ...
#
#   @ads.retry_on_failure()        mesure CHAQUE tentative séparément
#   @ads.timer
#   def methode(self): ...
#
# Voir logger/retry.py pour retry_on_failure.

# ---------------------------------------------------------------------------
# 6. set_timezone et now
# ---------------------------------------------------------------------------
print(f"Heure locale avant set_timezone : {datetime.now()}")

ads.set_timezone(tz="America/New_York")

# set_timezone a DEUX comportements selon le système, et c'est le point le
# plus important de cette section :
#
#   Unix     time.tzset() existe : la variable TZ est appliquée au
#            processus. datetime.now() ET ads.now() reflètent le nouveau
#            fuseau.
#   Windows  time.tzset() n'existe pas : le fuseau est SIMULÉ dans la
#            toolbox. datetime.now() continue de renvoyer l'heure locale
#            de la machine, seul ads.now() tient compte du réglage.
#
# Écrivez donc ads.now() partout, jamais datetime.now(), si le code doit
# être portable. La fonction le rappelle dans ses messages au lancement.
print(f"ads.now() après set_timezone   : {ads.now()}")
print(f"datetime.now() après           : {datetime.now()}  (identique sous Windows)")

# ads.now() renvoie toujours un datetime AVEC fuseau (timezone-aware) :
# soit celui défini par set_timezone, soit le fuseau local du système.
# Comparer un ads.now() à un datetime.now() nu lève un TypeError
# ("can't compare offset-naive and offset-aware datetimes").
maintenant = ads.now()
print(f"tzinfo présent : {maintenant.tzinfo}")

source.disconnect()