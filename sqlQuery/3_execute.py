from CommonLib import *

source_pg.connect()
source_pg.sqlExec(''' DROP TABLE IF EXISTS demo_insert ''')

source_pg.sqlExec('''
CREATE TABLE IF NOT EXISTS demo_insert (
    id SERIAL PRIMARY KEY,
    tenantname VARCHAR(255),
    fichier VARCHAR(255)
);''')

