"""
Env : chargement des variables d'environnement.

Aucun extra nécessaire : Env vit dans le cœur (paquet python-dotenv).
"""
import os
from dataclasses import dataclass
from pathlib import Path

import adsToolBox as ads
from adsToolBox.load_env import EnvError

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")

# ---------------------------------------------------------------------------
# 1. Recherche automatique du .env
# ---------------------------------------------------------------------------
# file=None (défaut) : Env remonte l'arborescence depuis le SCRIPT APPELANT
# jusqu'à trouver un .env. Les logs DEBUG tracent chaque dossier visité, ce
# qui est le meilleur moyen de comprendre pourquoi un .env n'est pas trouvé.
env = ads.Env(
    logger=logger,
    file=None,
)

# Si aucun .env n'est trouvé, Env n'échoue PAS : il émet deux warnings et
# continue avec les seules variables déjà présentes dans os.environ. Un
# script qui suppose un .env doit donc vérifier lui-même ses variables.

# ---------------------------------------------------------------------------
# 2. Pointer un fichier précis
# ---------------------------------------------------------------------------
# Utile quand plusieurs environnements coexistent, ou quand le script est
# lancé depuis un répertoire de travail imprévisible (ordonnanceur, cron).
env_explicite = ads.Env(
    logger=logger,
    file="../.env",  # relatif au répertoire courant, ou chemin absolu
)

# ---------------------------------------------------------------------------
# 3. Les trois façons de lire une variable
# ---------------------------------------------------------------------------
# a) En attribut. Concis, mais lève AttributeError si la variable manque et affole souvent les IDE.
#    PATH existe toujours, donc cet exemple tourne même sans .env.
print(env.PATH[:40])

# b) En indexation. Renvoie None si la variable est absente, jamais d'erreur.
print(env["PG_DWH_DB"])                 # None si le .env n'a pas été trouvé
print(env["VARIABLE_QUI_NEXISTE_PAS"])  # -> None

# c) Avec get() et une valeur de repli. C'est la forme à préférer pour tout
#    paramètre optionnel : elle rend le défaut visible dans le code.
print(env.get(item="PG_DWH_PORT", default="5432"))
print(env.get(item="TIMEOUT_ABSENT", default="30"))

# Attention : Env lit os.environ, donc get() et l'indexation renvoient
# toujours des CHAÎNES. Convertissez explicitement ce qui doit être numérique.
port = int(env.get(item="PG_DWH_PORT", default="5432"))
logger.info(f"Port utilisé : {port} ({type(port).__name__})")

# ---------------------------------------------------------------------------
# 4. Variable absente : les trois comportements côte à côte
# ---------------------------------------------------------------------------
try:
    print(env.VARIABLE_QUI_NEXISTE_PAS)
except AttributeError as e:
    logger.info(f"Accès en attribut -> AttributeError : {e}")

logger.info(f"Accès en indexation -> {env['VARIABLE_QUI_NEXISTE_PAS']}")
logger.info(f"Accès via get()     -> {env.get(item='VARIABLE_QUI_NEXISTE_PAS', default='repli')}")

# ---------------------------------------------------------------------------
# 5. Ce qu'Env expose
# ---------------------------------------------------------------------------
# Env donne accès à TOUT os.environ, pas seulement au contenu du .env. PATH,
# HOME et les variables système sont donc lisibles de la même façon.
#
# Depuis la 2026.10, la résolution se fait à l'ACCÈS et non par copie dans
# l'instance. Deux conséquences : une variable définie après la construction
# de l'objet est visible, et une variable en minuscules nommée comme une
# méthode (get, logger) n'écrase plus cette méthode. Auparavant un
# `export get=x` cassait l'objet en silence.
logger.info(f"env.get est bien une méthode : {callable(env.get)}")

# ---------------------------------------------------------------------------
# 6. bind() : une configuration typée et validée
# ---------------------------------------------------------------------------
# Les trois accès ci-dessus renvoient des chaînes, et une variable manquante
# ne se signale qu'au moment où on la lit. bind() construit à la place un
# objet typé, validé au DÉMARRAGE.


@dataclass
class PgConfig:
    """Configuration PostgreSQL attendue par ce script."""

    db: str
    user: str
    pwd: str
    port: int = 5432        # valeur par défaut si la variable est absente
    ssl: bool = False


# prefix évite de répéter PG_DWH_ dans chaque nom de champ : le champ `db`
# lit PG_DWH_DB, `port` lit PG_DWH_PORT, et ainsi de suite.
pg = env.bind(PgConfig, prefix="PG_DWH_")

logger.info(f"Configuration lue : {pg}")
logger.info(f"pg.port est un {type(pg.port).__name__}, donc pg.port + 1 = {pg.port + 1}")

# Types gérés : str, int, float, bool, Path, et les unions optionnelles
# (int | None). Pour les booléens, 1/true/vrai/yes/oui/on sont vrais,
# 0/false/faux/no/non/off sont faux, insensibles à la casse.


@dataclass
class ApiConfig:
    """Montre les autres conversions."""

    timeout: float
    cache: Path
    retries: int | None = None


os.environ["API_TIMEOUT"] = "2.5"
os.environ["API_CACHE"] = "/var/cache/api"
api = env.bind(ApiConfig, prefix="API_")
logger.info(f"Conversions variées : {api}")
# retries n'est pas dans l'environnement : la valeur par défaut None est gardée.


# ---------------------------------------------------------------------------
# 7. Validation : toutes les erreurs d'un coup
# ---------------------------------------------------------------------------
# C'est l'intérêt principal face à un AttributeError au premier usage : on
# corrige le .env en une fois au lieu de relancer le job à chaque variable
# manquante.
os.environ["BAD_PORT"] = "cinq-mille"
os.environ["BAD_SSL"] = "peut-etre"


@dataclass
class ConfigFautive:
    """Schéma volontairement non satisfait par l'environnement."""

    db: str
    user: str
    port: int
    ssl: bool


try:
    env.bind(ConfigFautive, prefix="BAD_")
except EnvError as e:
    logger.info(f"Quatre problèmes signalés ensemble :\n{e}")

# Un schéma qui n'est ni une dataclass ni un modèle pydantic est refusé
# explicitement. Les modèles pydantic sont acceptés si la bibliothèque est
# installée ; les dataclasses suffisent et n'ajoutent aucune dépendance.
try:
    env.bind(int)
except TypeError as e:
    logger.info(f"Schéma non supporté : {e}")