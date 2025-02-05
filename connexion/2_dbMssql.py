from CommonLib import *

# Instanciation d'une connexion à une base MSSQL
source = ads.dbMssql({'database':env.MSSQL_DWH_DB
                    , 'user':env.MSSQL_DWH_USER
                    , 'password':env.MSSQL_DWH_PWD
                    , 'port':env.MSSQL_DWH_PORT
                    , 'host':env.MSSQL_DWH_HOST
                    , 'charset': 'UTF-8'
                    , 'package': 'pytds' # 'pymssql par défaut
}, logger, 1)

#Connexion
source.connect()