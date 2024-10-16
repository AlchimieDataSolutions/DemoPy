import adsToolBox as ads
import time
import logging
import os
import threading

logger = ads.Logger(None, logging.DEBUG, "EnvLogger")
logger.info("Démo")

#Chargement des variables d'environnement
env = ads.env(logger) #,'C:/Users/ADS12/PycharmProjects/DemoPy/.env'

logger_connection = ads.dbPgsql({'database': env.PG_DWH_DB
                          , 'user': env.PG_DWH_USER
                          , 'password': env.PG_DWH_PWD
                          , 'port': env.PG_DWH_PORT
                          , 'host': env.PG_DWH_HOST},
                      None)
logger_connection.connect()
logger = ads.Logger(logger_connection, logging.INFO, "AdsLogger", "LOGS", "LOGS_details")
logger.info("Début de la démonstration...")
logger.disable()
ads.set_timer(True)

destination = {
    'name': 'test',
    'db': ads.dbPgsql({'database':env.PG_DWH_DB, 'user':env.PG_DWH_USER, 'password':env.PG_DWH_PWD, 'port':env.PG_DWH_PORT
                    , 'host':env.PG_DWH_HOST}, logger),
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