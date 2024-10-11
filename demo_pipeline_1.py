import adsGenericFunctions as ads

from env import *
import logging

logger_connection = ads.dbPgsql({'database': pg_dwh_db
                          , 'user': pg_dwh_user
                          , 'password': pg_dwh_pwd
                          , 'port': pg_dwh_port
                          , 'host': pg_dwh_host},
                      None)
logger_connection.connect()
logger = ads.Logger(logger_connection, logging.INFO, "AdsLogger", "LOGS", "LOGS_details")
logger.info("Début de la démonstration...")
logger.disable()
ads.set_timer(True)

# Déclarons une source base de données
source = ads.dbPgsql({'database':pg_dwh_db
                    , 'user':pg_dwh_user
                    , 'password':pg_dwh_pwd
                    , 'port':pg_dwh_port
                    , 'host':pg_dwh_host}, logger)

# Déclarer une destination, c'est un peu plus complexe
destination = {
    'db': ads.dbPgsql({'database':pg_dwh_db, 'user':pg_dwh_user, 'password':pg_dwh_pwd, 'port':pg_dwh_port
                    , 'host':pg_dwh_host}, logger),
    'table': 'demo_pipeline',
    'cols': ['tenantname', 'taille', 'unite', 'fichier']
}

# Créons la table de réception de nos données
destination['db'].connect()
destination['db'].sqlExec(''' DROP TABLE IF EXISTS demo_pipeline; ''')
destination['db'].sqlExec('''
CREATE TABLE IF NOT EXISTS demo_pipeline (
    id SERIAL PRIMARY KEY,
    tenantname VARCHAR(255),
    taille FLOAT(8),
    unite VARCHAR(10),
    fichier VARCHAR(255)
);
''')

# Voici la requête pour la source
query = '''
SELECT tenantname, taille, unite, fichier
FROM onyx_qs."diskcheck" LIMIT 5
'''
logger.enable()

# Premier pipeline
pipeline_1 = ads.pipeline({
    'db_source': source, # La source du pipeline
    'query_source': query, # La requête qui sera exécutée sur cette source
    'db_destinations': destination, # La destination du pipeline
}, logger)

rejects = pipeline_1.run() # pipeline.run() renvoie les rejets du pipeline, ce sera une liste vide s'il n'y en a pas
print(f"Rejets : {rejects}")

# Par défaut, batch_size est à 1, ce qui insère les lignes une par une, un batch_size plus grand implique un
# run plus rapide pour le même nombre de lignes
# Second pipeline
pipeline_2 = ads.pipeline({
    'db_source': source, # La source du pipeline
    'query_source': query, # La requête qui sera exécutée sur cette source
    'db_destinations': destination, # La destination du pipeline
    'batch_size': 50
}, logger)

rejects = pipeline_2.run()
print(f"Rejets : {rejects}")

logger.info("Fin de la démonstration")