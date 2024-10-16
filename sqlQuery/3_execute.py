from CommonLib import *

source = ads.dbPgsql({'database':env.PG_DWH_DB
                    , 'user':env.PG_DWH_USER
                    , 'password':env.PG_DWH_PWD
                    , 'port':env.PG_DWH_PORT
                    , 'host':env.PG_DWH_HOST}, logger, 1)

source.connect()

source.sqlExec(''' DROP TABLE IF EXISTS demo_insert ''')

source.sqlExec('''
CREATE TABLE IF NOT EXISTS demo_insert (
    id SERIAL PRIMARY KEY,
    tenantname VARCHAR(255),
    fichier VARCHAR(255)
);''')

