from CommonLib import *

# Déclarer une destination
destination = {
    'name': 'test',
    'db': source_mssql,
    'schema': 'dbo',
    'table': 'insert_test',
    'cols': ['name', 'email'],
    'conflict_cols': ['name'] # Paramètre à mettre si l'on compte faire un upsert
}

# Voici la requête pour la source (lecture des données)
query = '''
SELECT name, email FROM insert_test;
'''

# Déclaration du pipeline
pipe = ads.pipeline({
    'db_source': source_pg, # La source du pipeline
    'query_source': query, # La requête qui sera exécutée sur cette source
    'db_destination': destination, # La destination du pipeline
    'operation_type':'upsert', # Effectue un upsert, 'insert' par défaut
    'insert_method': 'executemany', # Applique des executemany, 'bulk' par défaut
    'batch_size': 5, # Optionnel, 10 000 par défaut
}, logger)

# On remplit la table source
rows = [(f'Name {i}', f'email{i}@example.com') for i in range(5)]
print(source_pg.insertBulk('', 'insert_test', ['name', 'email'], rows))

# pipeline.run() renvoie les résultats du pipeline
print(f"Résultats : {pipe.run()}")

logger.info("Fin de la démonstration")