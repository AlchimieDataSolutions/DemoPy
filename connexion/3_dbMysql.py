from CommonLib import *

# Instanciation d'une connexion à une base MySQL
source = ads.dbMysql({'database':env.MSYQL_DWH_DB
                    , 'user':env.MYSQL_DWH_USER
                    , 'password':env.MYSQL_DWH_PWD
                    , 'port':env.MYSQL_DWH_PORT
                    , 'host':env.MYSQL_DWH_HOST}, logger, 1)

#Connexion
source.connect()