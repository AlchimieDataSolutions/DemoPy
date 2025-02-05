import adsToolBox as ads
import os
import time
import threading
import shutil
import polars as pl

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

ads.set_timer(True)
logger = ads.Logger(ads.Logger.DEBUG, "AdsLogger")
logger.disable()
#Chargement des variables d'environnement
env = ads.env(logger, 'C:/Users/mvann/Desktop/ADS/Projects/Demo/.env')

source_pg = ads.dbPgsql({'database':env.PG_DWH_DB
                    , 'user':env.PG_DWH_USER
                    , 'password':env.PG_DWH_PWD
                    , 'port':env.PG_DWH_PORT
                    , 'host':env.PG_DWH_HOST}, logger)
source_pg.connect()

source_mssql = ads.dbMssql({'database': env.MSSQL_DWH_DB,
                      'user': env.MSSQL_DWH_USER,
                      'password': env.MSSQL_DWH_PWD,
                      'port': env.MSSQL_DWH_PORT_VPN,
                      'host': env.MSSQL_DWH_HOST_VPN}, logger)
source_mssql.connect()

logger.set_connection(source_pg, ads.Logger.DEBUG) # Attention ça réactive les logs donc
logger.disable()

source_pg.sqlExec('''
DROP TABLE IF EXISTS insert_test;
CREATE TABLE IF NOT EXISTS insert_test (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    age INT
);
''')

source_mssql.sqlExec('''
IF OBJECT_ID('dbo.insert_test', 'U') IS NOT NULL 
    DROP TABLE dbo.insert_test;
CREATE TABLE dbo.insert_test (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    age INT
);
''')

# Déclaration du pipeline
pipePgToSqlServer = ads.pipeline({
    'db_source': source_pg, # La source du pipeline
    'query_source': '''
    SELECT * FROM insert_test;
    ''', # La requête qui sera exécutée sur cette source
    'db_destination': {
    'name': 'test',
    'db': source_mssql,
    'schema': 'dbo',
    'table': 'insert_test',
    'cols': ['id', 'name', 'email', 'age']
}, # La destination du pipeline
}, logger)

logger.enable()