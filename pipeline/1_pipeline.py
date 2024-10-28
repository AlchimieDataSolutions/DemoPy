from CommonLib import *

# Déclarer une destination
destination = {
    'name': 'test',
    'db': source_mssql,
    'table': 'dbo.insert_test',
    'cols': ['name', 'email']
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
    'mode': 'executemany', # Applique des executemany, 'bulk' par défaut
    'batch_size': 5, # Optionnel, 10 000 par défaut
    'checkup': True, # vérifie ensuite si la destination correspond à la source après le run
}, logger)

# On remplit la table source
rows = [(f'Name {i}', f'email{i}@example.com') for i in range(5)]
print(source_pg.insertBulk('insert_test', ['name', 'email'], rows))

rejects = pipe.run() # pipeline.run() renvoie les rejets du pipeline, ce sera une liste vide s'il n'y en a pas
print(f"Rejets : {rejects}")

# Les deux batch_size sont à 1, chaque ligne sera inséré une par une, ce sera lent, mais les rejets seront des batchs
# de 1 ligne.
logger.info("Fin de la démonstration")