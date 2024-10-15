import adsToolBox as ads

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
ads.set_timer(True)
logger.disable()

# Déclarons une source base de données, mais cette fois ce sera un tableau
source = [
    ('ADS', 120.5, 'Mo', 'test1'),
    ('ADS', 130.7, 'Mo', 'test2'),
    ('ADS', 15.5, 'Mo', 'test3'),
    ('ADS', 100.0, 'Mo', 'test4')
]
destination = {
    'name': 'test',
    'db': ads.dbPgsql({'database':pg_dwh_db, 'user':pg_dwh_user, 'password':pg_dwh_pwd, 'port':pg_dwh_port
                    , 'host':pg_dwh_host}, logger),
    'table': 'demo_pipeline',
    'cols': ['tenantname', 'taille', 'unite', 'fichier']
}
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
logger.enable()

# Premier pipeline
pipe = ads.pipeline({
    'tableau': source, # Le tableau qui sert de source
    'db_destinations': destination, # La destination du pipeline
}, logger)

rejects = pipe.run()
print(f"{len(rejects)} rejet(s) : {rejects}")

# Voyons les rejets justement, redefinissons une source qui générera une erreur
source = [
    ('ADS', 120.5, 'Mo', 'test1'),
    ('ADS', 130.7, 'Mo', 'test2'),
    ('ADS', "Cela va créer une erreur", 'Mo', 'test3'),
    ('ADS', 100.0, 'Mo', 'test4')
]

# Premier pipeline, avec un batch_size de 1, seules les lignes qui posent problème ne seront pas insérées et
# seront dans rejets, les autres seront bien insérées
pipe = ads.pipeline({
    'tableau': source, # Le tableau qui sert de source
    'db_destinations': destination, # La destination du pipeline
    'batch_size': 1
}, logger)

rejects = pipe.run()
print(f"{len(rejects)} rejet(s) : {rejects}")

# Avec un batch_size plus grand, c'est le batch entier qui ne sera pas inséré et mis dans les rejets
# Second pipeline
pipe = ads.pipeline({
    'tableau': source, # Le tableau qui sert de source
    'db_destinations': destination, # La destination du pipeline
    'batch_size': 3
}, logger)

rejects = pipe.run()
print(f"{len(rejects)} rejet(s) : {rejects}")

logger.info("Fin de la démonstration")