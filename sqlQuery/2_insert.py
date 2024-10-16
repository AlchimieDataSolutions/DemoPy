from util import *

source = ads.dbPgsql({'database':env.PG_DWH_DB
                    , 'user':env.PG_DWH_USER
                    , 'password':env.PG_DWH_PWD
                    , 'port':env.PG_DWH_PORT
                    , 'host':env.PG_DWH_HOST}, logger, 1)

source.connect()

#Il existe également la fonction insertBulk
resultat = source.insert('''INSERT INTO onyx_qs."diskcheck" (tenantname, taille, unite, fichier) 
                 VALUES ('new_tenant', 0,'To', 'test3')''')

print(f"Resultat: {resultat}")