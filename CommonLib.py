import adsToolBox as ads
import time
import logging
import os
import threading

logger = ads.Logger(None, logging.DEBUG, "EnvLogger")

#Chargement des variables d'environnement
env = ads.env(logger) #,'C:/Users/ADS12/PycharmProjects/DemoPy/.env'

logger_connection = ads.dbPgsql({'database': env.PG_DWH_DB
                          , 'user': env.PG_DWH_USER
                          , 'password': env.PG_DWH_PWD
                          , 'port': env.PG_DWH_PORT
                          , 'host': env.PG_DWH_HOST},
                      None)
logger_connection.connect()
logger = ads.Logger(logger_connection, logging.DEBUG, "AdsLogger", "LOGS",
                    "LOGS_details")


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

def first(iterator, default=None):
    """
    Renvoie le premier élément d'un itérateur ou une valeur par défaut si l'itérateur est vide.
    :param iterator: Un objet itérable, une liste, un tuple etc.
    :param default: Valeur à renvoyer si l'itérateur est vide
    :return: Le premier élément de l'itérateur, ou `default` si l'itérateur est vide.
    """
    for item in iterator:
        return item
    return default

source_pg = ads.dbPgsql({'database':env.PG_DWH_DB
                    , 'user':env.PG_DWH_USER
                    , 'password':env.PG_DWH_PWD
                    , 'port':env.PG_DWH_PORT
                    , 'host':env.PG_DWH_HOST}, logger)

source_mssql = ads.dbMssql({'database': env.MSSQL_DWH_DB,
                      'user': env.MSSQL_DWH_USER,
                      'password': env.MSSQL_DWH_PWD,
                      'port': env.MSSQL_DWH_PORT_VPN,
                      'host': env.MSSQL_DWH_HOST_VPN}, logger)