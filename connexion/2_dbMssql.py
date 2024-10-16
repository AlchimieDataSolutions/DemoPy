from CommonLib import *

# Insranciation d'une base PostgreSQL
source = ads.dbMssql({'database':env.PG_DWH_DB
                    , 'user':env.PG_DWH_USER
                    , 'password':env.PG_DWH_PWD
                    , 'port':env.PG_DWH_PORT
                    , 'host':env.PG_DWH_HOST}, logger, 1)

#Connexion
source.connect()