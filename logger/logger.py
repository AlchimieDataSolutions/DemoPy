import os
import adsToolBox as ads

script_name = os.path.basename(__file__)

# Deux niveaux de logs existent, un pour l'affichage en console/fichier et un autre pour l'insertion en base
# timestamp_display et name_display font exactement ce que vous pensez et sont par défaut à True
logger = ads.Logger(
    logLevel = ads.Logger.DEBUG,
    logger_name = f"adsLogger - {script_name}",
    table_log_name="LOGS",
    table_log_details_name="LOGS_details",
    timestamp_display=True,
    name_display=True
)
env = ads.env(logger)

logger.info("Début de la démonstration.")

# Instanciation d'une connexion à une base PostgreSQL
source = ads.dbPgsql({'database':env.PG_DWH_DB
                    , 'user':env.PG_DWH_USER
                    , 'password':env.PG_DWH_PWD
                    , 'port':env.PG_DWH_PORT
                    , 'host':env.PG_DWH_HOST}, logger, 10)
source.connect() # Ne pas oublier de lancer la connexion
logger.set_connection(source, ads.Logger.DEBUG) # Tous les logs >= au niveau DEBUG seront insérés dans LOGS_details

# Si les tables de logs n'existent pas, il faut appeler
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

logger.enable(ads.Logger.DEBUG, ads.Logger.INFO) # Par défaut, se réactivent avec le niveau INFO

logger.info("Mais toi oui")
logger.debug("Et toi tu ne devrais t'afficher qu'en console/fichier")

# Avec chaque log généré avec un niveau supérieur ou égal, une ligne sera insérée dans la table LOGS_details
# Pour effectuer une insertion dans la table de logs principale, il faut appeler
logger.log_close("SUCCESS", "Message type")

# Attention log_close désactive les logs, logger.enable() les réactive
# Un job_key est créé à la déclaration du logger, ce qui permet de faire le lien entre les lignes de la table de logs
# principale et les lignes de la table de details, logger.enable() permet de créer un nouveau job_key