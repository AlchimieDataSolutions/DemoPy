"""
Le décorateur retry_on_failure.

Aucun extra nécessaire : retry_on_failure vit dans le cœur.
"""
import os

import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")

# retry_on_failure relance une méthode qui échoue, avec un délai entre les
# tentatives.
#
# À savoir : dans adsToolBox 2026.09.02, ce décorateur n'est utilisé en
# interne que par FileHandler (sur read_file, write_file, transfer_file,
# list_dir, file_exists, remove_file, disk_check...), avec
# retry_method="_set_connection" pour rétablir le backend fsspec.
#
# Les classes Db* ne l'utilisent PAS. Mais ce sera un ajout futur.

# ---------------------------------------------------------------------------
# 1. Où le décorateur trouve ses paramètres
# ---------------------------------------------------------------------------
# Il lit `retry_count` et `retry_delay` sur l'instance (self). Une classe qui
# veut être réessayable doit donc porter ces deux attributs. C'est pour cela
# que FileHandler les expose dans son __init__ et via set_retry_params().


class ServiceInstable:
    """Simule un service qui échoue les deux premières fois."""

    def __init__(self, logger: ads.Logger) -> None:
        self.logger = logger
        self.retry_count = 4      # nombre total de tentatives
        self.retry_delay = 0.2    # secondes entre deux tentatives
        self._appels = 0

    @ads.retry_on_failure()
    def appeler(self) -> str:
        """Échoue deux fois puis réussit."""
        self._appels += 1
        if self._appels < 3:
            msg = f"échec simulé n°{self._appels}"
            raise ConnectionError(msg)
        return f"réussi à la tentative {self._appels}"


service = ServiceInstable(logger)
logger.info(service.appeler())

# ---------------------------------------------------------------------------
# 2. Reconnexion entre deux tentatives
# ---------------------------------------------------------------------------
# `retry_method` nomme une méthode à rappeler avant chaque nouvelle tentative.


class ServiceAvecReconnexion:
    """Illustre retry_method, appelée avant chaque nouvelle tentative."""

    def __init__(self, logger: ads.Logger) -> None:
        self.logger = logger
        self.retry_count = 3
        self.retry_delay = 0.1
        self._appels = 0
        self.reconnexions = 0

    def _reconnecter(self) -> None:
        """Méthode de reconnexion, rappelée par le décorateur."""
        self.reconnexions += 1
        self.logger.debug(f"reconnexion n°{self.reconnexions}")

    @ads.retry_on_failure(retry_method="_reconnecter")
    def appeler(self) -> str:
        """Échoue une fois puis réussit."""
        self._appels += 1
        if self._appels < 2:
            msg = "connexion perdue"
            raise ConnectionError(msg)
        return "réussi après reconnexion"


service2 = ServiceAvecReconnexion(logger)
logger.info(service2.appeler())

# ---------------------------------------------------------------------------
# 3. Épuisement des tentatives
# ---------------------------------------------------------------------------
# Une fois retry_count atteint, la dernière exception est propagée telle
# quelle : le décorateur ne l'avale pas. À l'appelant de la traiter.


class ServiceMort:
    """Échoue toujours, pour illustrer la propagation finale."""

    def __init__(self, logger: ads.Logger) -> None:
        self.logger = logger
        self.retry_count = 2
        self.retry_delay = 0.1

    @ads.retry_on_failure()
    def appeler(self) -> None:
        """Échoue systématiquement."""
        msg = "service définitivement indisponible"
        raise ConnectionError(msg)


try:
    ServiceMort(logger).appeler()
except ConnectionError as e:
    logger.info(f"Exception bien propagée après épuisement des tentatives : {e}")

# ---------------------------------------------------------------------------
# 4. Sur une fonction libre : paramètres obligatoires
# ---------------------------------------------------------------------------
# Hors classe il n'y a pas de `self` porteur de retry_count/retry_delay. Le
# décorateur ne prend PAS de valeurs par défaut dans ce cas : il faut les lui
# passer, sinon il lève un ValueError explicite.
#
#   @ads.retry_on_failure()            ->  ValueError: retry_count et
#                                          retry_delay sont requis.

_essais = {"n": 0}


@ads.retry_on_failure(retry_count=3, retry_delay=0.1)
def fonction_libre(logger: ads.Logger = None) -> str:
    """Fonction hors classe : les paramètres viennent du décorateur."""
    _essais["n"] += 1
    if _essais["n"] < 2:
        msg = "premier essai raté"
        logger.error(msg)
        raise ConnectionError(msg)
    return "fonction libre réussie"

logger.info(fonction_libre(logger=logger))

# Les paramètres passés au décorateur ont priorité sur ceux de l'instance,
# ce qui permet de durcir ou d'assouplir une méthode précise sans toucher aux
# attributs de la classe.

# ---------------------------------------------------------------------------
# 5. Ne réessayer que certaines exceptions
# ---------------------------------------------------------------------------
# Par défaut toute Exception déclenche un nouvel essai. Réessayer une erreur
# de programmation (KeyError, TypeError) est inutile et masque le bug :
# `retryable_exceptions` restreint le filet.


class ServiceSelectif:
    """Ne réessaie que les erreurs réseau."""

    def __init__(self, logger: ads.Logger) -> None:
        self.logger = logger
        self.retry_count = 3
        self.retry_delay = 0.1

    @ads.retry_on_failure(retryable_exceptions=(ConnectionError, TimeoutError))
    def bug_de_code(self) -> None:
        """Lève une exception hors périmètre : aucune nouvelle tentative."""
        msg = "clef absente du dictionnaire"
        raise KeyError(msg)


try:
    ServiceSelectif(logger).bug_de_code()
except KeyError:
    logger.info("KeyError propagée immédiatement, sans nouvelle tentative.")

# ---------------------------------------------------------------------------
# 6. retry_count=0 signifie INFINI
# ---------------------------------------------------------------------------
# Attention au contre-intuitif : 0 ne veut pas dire « aucune tentative » mais
# « réessayer indéfiniment ». Utile pour un démon qui doit attendre qu'un
# service revienne, dangereux dans un batch ordonnancé qui ne rendra jamais
# la main. Ne l'utilisez qu'avec un délai franc et un log visible.
#
#   @ads.retry_on_failure(retry_count=0, retry_delay=30)

# ---------------------------------------------------------------------------
# 7. Combiner avec @ads.timer
# ---------------------------------------------------------------------------
# L'ordre compte. @timer au-dessus de @retry_on_failure chronomètre
# l'ensemble des tentatives ; en dessous, chaque tentative séparément.
# Voir logger/timer.py pour le détail du chronométrage.