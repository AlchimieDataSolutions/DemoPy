from CommonLib import *

logger.enable()
source_pg.connect()
print(source_pg.insert('', 'demo_insert', ['tenantname', 'fichier'], ['tenant_example', 'file_example']))

rows_100 = [(f'Name {i}', f'email{i}@example.com') for i in range(100)]
print(source_pg.insertMany('', 'insert_test', ['name', 'email'], rows_100))

rows_50k = [(f'Name {i}', f'email{i}@example.com') for i in range(50_000)]
print(source_pg.insertBulk('', 'insert_test', ['name', 'email'], rows_50k))

logger.warning("Et avec une connexion SQL Server via pymssql?")

source_mssql = ads.dbMssql({'database': env.MSSQL_DWH_DB,
                      'user': env.MSSQL_DWH_USER,
                      'password': env.MSSQL_DWH_PWD,
                      'port': env.MSSQL_DWH_PORT_VPN,
                      'host': env.MSSQL_DWH_HOST_VPN,
                            'package': 'pymssql'}, logger)
source_mssql.connect()
print(source_mssql.insert('dbo', 'insert_test', ['name', 'email'], ['nom', 'mail']))

print(source_mssql.insertMany('dbo', 'insert_test', ['name', 'email'], rows_100))

print(source_mssql.insertBulk('dbo', 'insert_test', ['name', 'email'], rows_50k))

logger.warning("Et avec une connexion SQL Server via pytds?")

source_mssql = ads.dbMssql({'database': env.MSSQL_DWH_DB,
                      'user': env.MSSQL_DWH_USER,
                      'password': env.MSSQL_DWH_PWD,
                      'port': env.MSSQL_DWH_PORT_VPN,
                      'host': env.MSSQL_DWH_HOST_VPN,
                            'package': 'pytds'}, logger)
source_mssql.connect()
print(source_mssql.insert('dbo', 'insert_test', ['name', 'email'], ['nom', 'mail']))

print(source_mssql.insertMany('dbo', 'insert_test', ['name', 'email'], rows_100))

print(source_mssql.insertBulk('dbo', 'insert_test', ['name', 'email'], rows_50k))

logger.warning("Et avec une connexion MySQL?")