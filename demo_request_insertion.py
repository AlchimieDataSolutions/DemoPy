import adsGenericFunctions as ads

from env import *
import logging
import psycopg2

# On établit une connexion pour le logger pour qu'il puisse écrire en base
logger_connection = psycopg2.connect(database=pg_dwh_db, user=pg_dwh_user, password=pg_dwh_pwd, port=pg_dwh_port,
                                     host=pg_dwh_host)
logger = ads.Logger(logger_connection, logging.INFO, "AdsLogger", "LOGS", "LOGS_details")
logger.info("Début de la démonstration...")

# On active le timer, les requêtes seront chronométrées
ads.set_timer(True)

# On définit une source de connexion à laquelle on affecte notre logger
source = ads.dbPgsql({'database': pg_dwh_db, 'user': pg_dwh_user, 'password': pg_dwh_pwd, 'port': pg_dwh_port,
                      'host': pg_dwh_host}, logger)
source.connect()

# On crée une table
source.exec('''
CREATE TABLE IF NOT EXISTS demo_insert (
    id SERIAL PRIMARY KEY,
    tenantname VARCHAR(255),
    fichier VARCHAR(255)
);
''')
logger.info("Table créee avec succès.")

# Insertion d'une ligne
source.insert('demo_insert', ['tenantname', 'fichier'], ['tenant_example', 'file_example'])

# Insertion de plusieurs lignes
rows_to_insert = [
    ('tenant1', 'file1.txt'),
    ('tenant2', 'file2.txt'),
    ('tenant3', 'file3.txt')
]
source.insertBulk('demo_insert', ['tenantname', 'fichier'], rows_to_insert)

# Lisons cette même table
data = source.sqlQuery(''' SELECT * FROM demo_insert ''')
print(list(data))

# Suppression de la table
source.exec(''' DROP TABLE demo_insert ''')
logger.info("Fin de la démonstration.")