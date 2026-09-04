"""
Env : chargement des variables d'environnement.

Aucun extra nécessaire : Env vit dans le cœur (paquet python-dotenv).
"""
import os

import adsToolBox as ads

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
    file=".env",  # relatif au répertoire courant, ou chemin absolu
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
# Env copie TOUT os.environ en attributs de l'instance, pas seulement le
# contenu du .env. PATH, HOME et les variables système sont donc accessibles
# de la même façon.
logger.info(f"Nombre de variables exposées : {len(vars(env))}")