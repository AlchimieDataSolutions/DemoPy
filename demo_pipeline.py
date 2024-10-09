import adsGenericFunctions as ads

from env import *
import logging

logger_connection = ads.dbPgsql({'database': pg_dwh_db,
                                 'user': pg_dwh_user,
                                 'password': pg_dwh_pwd,
                                 'port': pg_dwh_port,
                                 'host': pg_dwh_host}, None)
logger_connection.connect()
logger = ads.Logger(logger_connection, logging.INFO, "AdsLogger", "LOGS", "LOGS_details")
logger.info("Début de la démonstration.")
logger.disable()
ads.set_timer(True)

# Déclarons une source base de données et une destination base de données
source = ads.dbPgsql({'database':pg_dwh_db
                    , 'user':pg_dwh_user
                    , 'password':pg_dwh_pwd
                    , 'port':pg_dwh_port
                    , 'host':pg_dwh_host}, logger)
destination = ads.dbPgsql({'database':pg_dwh_db
                    , 'user':pg_dwh_user
                    , 'password':pg_dwh_pwd
                    , 'port':pg_dwh_port
                    , 'host':pg_dwh_host}, logger)

# Créons la table de réception de nos données
destination.connect()
destination.sqlExec(''' DROP TABLE IF EXISTS demo_pipeline ''')
destination.sqlExec('''
CREATE TABLE IF NOT EXISTS demo_pipeline (
    id SERIAL PRIMARY KEY,
    tenantname VARCHAR(255),
    taille FLOAT(8),
    unite VARCHAR(10),
    fichier VARCHAR(255)
);''')

# Voici la requête qui sera exécutée sur la source
query = '''
SELECT tenantname, taille, unite, fichier
FROM onyx_qs."diskcheck" LIMIT 5
'''
logger.enable()

# Premier pipeline
pipe = ads.pipeline({
    'db_source': source, # La source du pipeline
    'query_source': query, # La requête qui sera exécutée sur cette source
    'db_destination': destination, # La destination du pipeline
    'table': 'demo_pipeline', # La tbale de destination
    'cols': ['tenantname', 'taille', 'unite', 'fichier'] # Les colonnes où nous allons insérer
}, logger)

# Le run renvoie les rejets de l'opération, ce sera donc une liste vide si rien n'est rejeté
rejects = pipe.run()
print(f"Rejet(s): {rejects}")

# Par défaut, le batch_size est de 1, ce qui insère les lignes une par une, un batch_size plus grand implique un run
# plus rapide pour le même nombre de lignes
# Second pipeline
pipe = ads.pipeline({
    'db_source': source, # La source du pipeline
    'query_source': query, # La requête qui sera exécutée sur cette source
    'db_destination': destination, # La destination du pipeline
    'table': 'demo_pipeline', # La tbale de destination
    'cols': ['tenantname', 'taille', 'unite', 'fichier'], # Les colonnes où nous allons insérer
    'batch_size': 50
}, logger)

rejects = pipe.run()
print(f"Rejet(s): {rejects}")

logger.info("Fin de la démonstration")