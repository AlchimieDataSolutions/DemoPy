import utils
import os
import adsToolBox as ads

script_name = os.path.basename(__file__)

# Les niveaux de logs sont définis par des int, 10 : DEBUG, 20 : INFO, 30 : WARNING, 40 : ERROR
# Ils sont utilisés de deux façons différentes, pour l'affichage en console/fichier et pour l'insertion en base
# Les logs en fichier ont un turnover de 10 jours au-délà duquel les plus anciens seront supprimés
logger = ads.Logger(
    log_level = ads.Logger.DEBUG, # Niveau de log à l'initialisation, chaque message au-dessus sera affiché
    logger_name = f"adsLogger - {script_name}", # Nom du logger (important pour le threading)
    table_log_name = "LOGS", # Nom de la table de log principale
    table_log_details_name = "LOGS_details", # Nom de la table de détails
    timestamp_display=True, # Affiche l'horodatage
    name_display=True # Affiche le nom du logger
)
env = ads.Env(logger)

logger.info("Début de la démonstration.")

# Instanciation d'une connexion à une base PostgreSQL
source = ads.DbPgsql({'database':env.PG_DWH_DB
                    , 'user':env.PG_DWH_USER
                    , 'password':env.PG_DWH_PWD
                    , 'port':env.PG_DWH_PORT
                    , 'host':env.PG_DWH_HOST}, logger, 10)
source.connect() # Ne pas oublier de lancer la connexion

logger.set_connection(
    source, # La base dans laquelle on insère
    ads.Logger.DEBUG, # Tous les logs >= DEBUG seront insérés dans la table LOGS_details
)

# Si les tables de logs n'existent pas, il faut appeler (échoue si elles existent)
logger.create_logs_tables()

logger.debug("Message de debug")
logger.info("Message d'info")
logger.warning("Message de warning")
logger.error("Message d'erreur")
logger.custom_log(25, "Message avec niveau custom")

# Cette commande désactive l'affichage des logs et l'insertion des logs en base et renvoie les niveaux de logs
# qui étaient définis (au cas où l'interruption est temporaire par exemple)
file_logger, base_logger = logger.disable()

logger.info("Toi tu ne t'afficheras pas")

logger.enable(ads.Logger.DEBUG, ads.Logger.INFO) # Par défaut, se réactive avec le niveau INFO

logger.info("Mais toi oui")
logger.debug("Et toi tu ne devrais t'afficher qu'en console/fichier")

# Avec chaque log généré avec un niveau supérieur ou égal, une ligne sera insérée dans la table LOGS_details
# Pour effectuer une insertion dans la table de logs principale, il faut appeler
logger.log_close("SUCCESS", "Message type")

# Attention log_close désactive les logs, logger.enable() les réactive
# Un job_key est créé à la déclaration du logger, ce qui permet de faire le lien entre les lignes de la table de logs
# principale et les lignes de la table de details
# Le param generate_new_key de logger.enable permet de regénerer un nouveau job_key