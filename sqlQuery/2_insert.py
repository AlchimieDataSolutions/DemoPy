from CommonLib import *

logger.enable()
source_pg.connect()
print(source_pg.insert('demo_insert', ['tenantname', 'fichier'], ['tenant_example', 'file_example']))

rows_100 = [(f'Name {i}', f'email{i}@example.com') for i in range(100)]
print(source_pg.insertMany('insert_test', ['name', 'email'], rows_100))

rows_50k = [(f'Name {i}', f'email{i}@example.com') for i in range(50_000)]
print(source_pg.insertBulk('insert_test', ['name', 'email'], rows_50k))

logger.warning("Et avec une connexion SQL Server?")

source_mssql.connect()
print(source_mssql.insert('insert_test', ['name', 'email'], ['nom', 'mail']))

print(source_mssql.insertMany('insert_test', ['name', 'email'], rows_100))

print(source_mssql.insertBulk('insert_test', [2, 3], rows_50k))
# insertBulk de dbMssql prend les indices des colonnes dans lesquelles insérer, pas les noms
