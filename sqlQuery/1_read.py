from util import *

source = ads.dbPgsql({'database':env.PG_DWH_DB
                    , 'user':env.PG_DWH_USER
                    , 'password':env.PG_DWH_PWD
                    , 'port':env.PG_DWH_PORT
                    , 'host':env.PG_DWH_HOST}, logger, 1)

source.connect()

data = source.sqlQuery('''SELECT tenantname, taille, unite, fichier
                   FROM onyx_qs."diskcheck" LIMIT 5''')

for i in data:
    print(i)