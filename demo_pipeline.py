import adsGenericFunctions as ads

from env import *
import logging
import psycopg2

# On établit une connexion pour le logger pour qu'il puisse écrire en base
logger_connection = psycopg2.connect(database=pg_dwh_db, user=pg_dwh_user, password=pg_dwh_pwd, port=pg_dwh_port,
                                     host=pg_dwh_host)
logger = ads.Logger(logger_connection, logging.INFO, "AdsLogger", "LOGS", "LOGS_details")
logger.info("Début de la démonstration...")

# On active le timer, les requêtes seront chronométrées
ads.set_timer(True)

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
destination.connect()
destination.exec('''
CREATE TABLE IF NOT EXISTS demo_pipeline (
    id SERIAL PRIMARY KEY,
    tenantname VARCHAR(255),
    taille FLOAT(8),
    unite VARCHAR(10),
    fichier VARCHAR(255)
);
''')

query = '''
SELECT tenantname, taille, unite, fichier
FROM onyx_qs."diskcheck" LIMIT 10
'''

# Attention si on passe une liste de lignes à insérer à un pipeline simple, elles seront insérées une par une
# Loguée une par une et timée une par une
pipeline = ads.pipeline({'db_source': source, 'query_source': query, 'db_destination': destination,
                         'table': 'demo_pipeline', 'cols': ['tenantname', 'taille', 'unite', 'fichier']}, logger)
pipeline.run()

# Si vous voulez insérer plusieurs lignes, utilisez plutôt
pipelineBulk = ads.pipelineBulk({'db_source': source, 'query_source': query, 'db_destination': destination,
                         'table': 'demo_pipeline', 'cols': ['tenantname', 'taille', 'unite', 'fichier']}, logger)
pipelineBulk.run()

# Et si la source est un tableau

source = [
    ('ADS', 120.5, 'Mo', 'test1'),
    ('ADS', 130.7, 'Mo', 'test2'),
    ('ADS', 140.9, 'Mo', 'test3'),
    ('ADS', 100.0, 'Mo', 'test4')
]

# Attention si on passe une liste de lignes à insérer à un pipelineTableau simple, elles seront insérées une par
# une, loguée une par une et timée une par une
pipeline = ads.pipelineTableau({'tableau': source, 'db_destination': destination, 'table': 'demo_pipeline',
                 'cols': ['tenantname', 'taille', 'unite', 'fichier']}, logger)
pipeline.run()




# Si vous voulez insérer plusieurs lignes, utilisez plutôt
pipelineBulk = ads.pipelineTableauBulk({'tableau': source, 'db_destination': destination, 'table': 'demo_pipeline',
                 'cols': ['tenantname', 'taille', 'unite', 'fichier']}, logger)
pipelineBulk.run()

# Supprimons la table
destination.exec(''' DROP TABLE demo_pipeline ''')
logger.info("Fin de la démonstration")