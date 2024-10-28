import adsToolBox as ads
import logging

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

source_pg = ads.dbPgsql({'database':env.PG_DWH_DB
                    , 'user':env.PG_DWH_USER
                    , 'password':env.PG_DWH_PWD
                    , 'port':env.PG_DWH_PORT
                    , 'host':env.PG_DWH_HOST}, logger)

source_mssql = ads.dbMssql({'database': env.MSSQL_DWH_DB,
                      'user': env.MSSQL_DWH_USER,
                      'password': env.MSSQL_DWH_PWD,
                      'port': env.MSSQL_DWH_PORT,
                      'host': env.MSSQL_DWH_HOST}, logger)

source_pg.connect()
source_pg.sqlExec('''
DROP TABLE IF EXISTS insert_test;
CREATE TABLE IF NOT EXISTS insert_test (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255)
);
''')

source_mssql.connect()
source_mssql.sqlExec('''
IF OBJECT_ID('dbo.insert_test', 'U') IS NOT NULL 
    DROP TABLE dbo.insert_test;

CREATE TABLE dbo.insert_test (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255)
);
''')

# Déclaration du pipeline
pipePgToSqlServer = ads.pipeline({
    'db_source': source_pg, # La source du pipeline
    'query_source': '''
SELECT id, name, email FROM insert_test;
''', # La requête qui sera exécutée sur cette source
    'db_destination': {
    'name': 'test',
    'db': source_mssql,
    'table': 'dbo.insert_test',
    'cols': [1, 2, 3]
}, # La destination du pipeline
}, logger)