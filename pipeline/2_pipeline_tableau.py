from CommonLib import *

# Déclarons une source base de données, mais cette fois ce sera un tableau
source = [
    ('Nom 1', 'Email 1', 1),
    ('Nom 2', 'Email 2', 2),
    ('Nom 3', 'Email 3', "ERR"),
    ('Nom 4', 'Email 4', 4)
]

destination = {
    'name': 'test',
    'db': source_mssql,
    'schema': 'dbo',
    'table': 'insert_test',
    'cols': ['name', 'email', 'age']
}

# Déclaration du pipeline
pipe = ads.pipeline({
    'tableau': source, # Le tableau qui sert de source
    'db_destination': destination,
    'mode': 'executemany',
    'batch_size': 1, # Optionnel, 10 000 par défaut
}, logger)

print(f"Résultats : {pipe.run()}")
logger.info("Fin de la démonstration")