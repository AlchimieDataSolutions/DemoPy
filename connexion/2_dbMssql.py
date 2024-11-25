from CommonLib import *

# Instanciation d'une base PostgreSQL
source = ads.dbMssql({'database':env.MSSQL_DWH_DB
                    , 'user':env.MSSQL_DWH_USER
                    , 'password':env.MSSQL_DWH_PWD
                    , 'port':env.MSSQL_DWH_PORT
                    , 'host':env.MSSQL_DWH_HOST}, logger, 1)

#Connexion
source.connect()