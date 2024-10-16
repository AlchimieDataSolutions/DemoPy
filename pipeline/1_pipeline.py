from CommonLib import *

# Déclarons une source base de données
source = ads.dbPgsql({'database':env.PG_DWH_DB
                    , 'user':env.PG_DWH_USER
                    , 'password':env.PG_DWH_PWD
                    , 'port':env.PG_DWH_PORT
                    , 'host':env.PG_DWH_HOST}
                    ,logger
                    , 1) # Optionnel, 10 000 par défaut

# Déclarer une destination
destination = {
    'name': 'test',
    'db': ads.dbPgsql({'database':env.PG_DWH_DB, 'user':env.PG_DWH_USER, 'password':env.PG_DWH_PWD, 'port':env.PG_DWH_PORT
                    , 'host':env.PG_DWH_HOST}, logger),
    'table': 'demo_pipeline',
    'cols': ['tenantname', 'taille', 'unite', 'fichier']
}

# Voici la requête pour la source (lecture des données)
query = '''
SELECT tenantname, taille, unite, fichier
FROM onyx_qs."diskcheck" LIMIT 5
'''

# Déclaration du pipeline
pipe = ads.pipeline({
    'db_source': source, # La source du pipeline
    'query_source': query, # La requête qui sera exécutée sur cette source
    'db_destination': destination, # La destination du pipeline
    'batch_size': 1, # Optionnel, 10 000 par défaut
}, logger)

rejects = pipe.run() # pipeline.run() renvoie les rejets du pipeline, ce sera une liste vide s'il n'y en a pas
print(f"Rejets : {rejects}")

# Les deux batch_size sont à 1, chaque ligne sera inséré une par une, ce sera lent, mais les rejets seront des batchs
# de 1 ligne.

logger.info("Fin de la démonstration")