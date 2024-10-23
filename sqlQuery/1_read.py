from CommonLib import *

source = ads.dbPgsql({'database':env.PG_DWH_DB
                    , 'user':env.PG_DWH_USER
                    , 'password':env.PG_DWH_PWD
                    , 'port':env.PG_DWH_PORT
                    , 'host':env.PG_DWH_HOST}, logger, 5)

source.connect()
data = source.sqlQuery('''SELECT tenantname, taille, unite, fichier
                   FROM onyx_qs."diskcheck" LIMIT 5''')
for i in data:
    print(i)

logger.warning("Et une connexion SQL Server?")
source = ads.dbMssql({'database': env.MSSQL_DWH_DB,
                      'user': env.MSSQL_DWH_USER,
                      'password': env.MSSQL_DWH_PWD,
                      'port': env.MSSQL_DWH_PORT_VPN,
                      'host': env.MSSQL_DWH_HOST_VPN}, logger, 5)
source.connect()
data = source.sqlQuery('''SELECT TOP 5 * FROM "dbo"."insert_test";''')
for i in data:
    print(i)