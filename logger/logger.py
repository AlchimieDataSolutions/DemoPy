# adstoolbox[pgsql]
"""
Logger : niveaux, insertion en base, activation/désactivation.

L'extra pgsql n'est requis que pour la partie insertion en base
(sections 4 et suivantes). Les sections 1 à 3 tournent sans aucun extra.
"""
import os

import adsToolBox as ads

script_name = os.path.basename(__file__)

# ---------------------------------------------------------------------------
# 1. Instanciation
# ---------------------------------------------------------------------------
# Les niveaux sont des int : 10 DEBUG, 20 INFO, 30 WARNING, 40 ERROR,
# 50 CRITICAL. Ils servent à DEUX filtrages distincts, gérés séparément :
# l'affichage console/fichier, et l'insertion en base.
# Le fichier de log tourne quotidiennement et garde 10 jours d'historique.
logger = ads.Logger(
    log_level=ads.Logger.DEBUG,                  # seuil initial pour les deux filtrages
    logger_name=f"adsLogger - {script_name}",    # important en contexte multi-thread
    table_log_name="LOGS",                       # table de log principale
    table_log_details_name="LOGS_details",       # table de détails, une ligne par message
    timestamp_display=True,                      # affiche l'horodatage
    name_display=True,                           # affiche le nom du logger
    enable_console=True,                         # handler console
    enable_file=True,                            # handler fichier (log.txt)
)

# enable_console=False et enable_file=False donnent un logger muet côté
# affichage mais qui continue d'insérer en base : utile pour un job planifié
# dont on ne veut que la trace en table.

logger.info("Début de la démonstration.")

# ---------------------------------------------------------------------------
# 2. Les cinq méthodes de log
# ---------------------------------------------------------------------------
logger.debug(message="Message de debug")
logger.info(message="Message d'info")
logger.warning(message="Message de warning")
logger.error(message="Message d'erreur")

# custom_log accepte n'importe quel niveau entier, y compris entre deux
# niveaux standards. Pratique pour un palier maison (25 = "notice").
logger.custom_log(log_level=25, message="Message avec niveau custom")

# error() se distingue des autres : il encadre le message de lignes d'astérisques
# et, si une exception est en cours, joint automatiquement le traceback au
# message inséré en base.
try:
    _ = 1 / 0
except ZeroDivisionError:
    logger.error(message="Erreur avec traceback joint en base")

# ---------------------------------------------------------------------------
# 3. Le paramètre insert : logger sans écrire en base
# ---------------------------------------------------------------------------
# info, warning et error acceptent insert=False. Le message part en
# console/fichier mais PAS dans LOGS_details. Deux usages :
#   - éviter de polluer la table avec des messages de progression verbeux ;
#   - éviter une récursion quand on logue une erreur d'insertion de log.
logger.info(message="Visible en console, absent de la base", insert=False)

# debug() n'a pas ce paramètre : il insère toujours si le niveau le permet.

# ---------------------------------------------------------------------------
# 4. Connexion à la base
# ---------------------------------------------------------------------------
env = ads.Env(logger=logger)

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
source.connect()  # à ne pas oublier : set_connection ne connecte pas

logger.set_connection(
    ads_connection=source,          # instance Db*
    log_level=ads.Logger.DEBUG,     # seuil D'INSERTION, indépendant de l'affichage
)

# ATTENTION : set_connection appelle create_logs_tables() lui-même. Les deux
# tables sont donc créées dès cet appel. Si elles existent déjà, un warning
# "Tables de logs déjà existantes" est émis et le traitement continue.
#
# create_logs_tables() reste public et peut être rappelé, mais c'est
# redondant après set_connection : il tenterait une seconde création.
# logger.create_logs_tables()   # <- inutile ici

# Les types SQL sont choisis selon la classe de connexion (TIMESTAMP/UUID pour
# Postgres, DATETIME/UNIQUEIDENTIFIER pour SQL Server, DATETIME/CHAR(36) pour
# MySQL). Une connexion d'un type non reconnu lève NotImplementedError.

# ---------------------------------------------------------------------------
# 5. Deux seuils indépendants
# ---------------------------------------------------------------------------
# À partir d'ici, chaque message de niveau >= DEBUG génère une ligne dans
# LOGS_details, en plus de l'affichage.
logger.debug(message="Inséré en base ET affiché")

# ---------------------------------------------------------------------------
# 6. Couper les logs : disable / enable
# ---------------------------------------------------------------------------
# disable() coupe l'affichage ET l'insertion, et RENVOIE les deux seuils
# précédents pour pouvoir les rétablir à l'identique.
niveau_affichage, niveau_base = logger.disable()

logger.info(message="Toi tu ne t'afficheras pas")

# enable() sans argument repart à INFO pour les deux : pensez à repasser les
# valeurs récupérées si l'interruption était temporaire.
logger.enable(
    level_logger=niveau_affichage,   # seuil console/fichier
    level_for_base=niveau_base,      # seuil d'insertion
    generate_new_key=False,          # conserve le job_key courant
)

logger.info(message="Mais moi oui")

# Deux seuils différents : DEBUG en console, INFO en base.
logger.enable(level_logger=ads.Logger.DEBUG, level_for_base=ads.Logger.INFO)
logger.debug(message="Affiché en console, pas inséré en base")

# ---------------------------------------------------------------------------
# 7. disabled() : le gestionnaire de contexte
# ---------------------------------------------------------------------------
# Plus sûr que disable()/enable() à la main : les seuils sont rétablis même
# si une exception survient dans le bloc. C'est ce que FileHandler utilise
# en interne pour taire les logs d'un transfert imbriqué.
with logger.disabled():
    logger.info(message="Silencieux, quoi qu'il arrive dans le bloc")

logger.info(message="Les seuils sont rétablis automatiquement")

# Même en cas d'exception :
try:
    with logger.disabled():
        msg = "échec au milieu du bloc"
        raise RuntimeError(msg)
except RuntimeError:
    logger.info(message="Seuils rétablis malgré l'exception")

# ---------------------------------------------------------------------------
# 8. Clore le job : log_close et job_key
# ---------------------------------------------------------------------------
# Un job_key (UUID) est généré à la création du logger. Il est écrit dans
# chaque ligne de LOGS_details, ce qui permet de relier les détails à la
# ligne de synthèse de LOGS.
logger.info(message=f"job_key courant : {logger.job_key}", insert=False)

# log_close insère LA ligne de synthèse dans LOGS (heure de début, heure de
# fin, chemin du script, statut, message) puis DÉSACTIVE les logs.
logger.log_close(
    status="SUCCESS",           # texte libre : SUCCESS, ERROR, PARTIAL...
    message="Message type",
)

# Après log_close, plus rien ne s'affiche ni ne s'insère.
logger.info(message="Invisible : log_close a désactivé les logs")

# Pour enchaîner sur un second job dans le même processus, réactivez avec un
# nouveau job_key, sinon les deux jobs partageraient la même clé.
logger.enable(
    level_logger=ads.Logger.DEBUG,
    level_for_base=ads.Logger.INFO,
    generate_new_key=True,      # nouveau job_key ET nouvelle date de création
)
logger.info(message=f"Nouveau job_key : {logger.job_key}", insert=False)