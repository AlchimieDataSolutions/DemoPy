from CommonLib import *

query = "SELECT name, email, age FROM insert_test"

comparator = ads.dataComparator({
    'db_source_1': source_pg,
    'db_source_2': source_mssql,
    'query_source_1': query,
    'query_source_2': query
}, logger)

rows = [(f'Name {i}', f'email{i}@example.com', i) for i in range(1, 6)]
print(source_pg.insertBulk('', 'insert_test', ['name', 'email', 'age'], rows))

rejects = pipePgToSqlServer.run()
print(f"Rejets : {rejects}")

# Les deux tables devraient être égales donc pas d'erreur générée
comparator.compare()

logger.info("Fin de la démonstration")