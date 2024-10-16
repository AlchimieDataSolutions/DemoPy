from util import *

# Déclarons une source base de données, mais cette fois ce sera un tableau
source = [
    ('ADS', 120.5, 'Mo', 'test1'),
    ('ADS', 130.7, 'Mo', 'test2'),
    ('ADS', "Cela va créer une erreur", 'Mo', 'test3'),
    ('ADS', 100.0, 'Mo', 'test4')
]
destination = {
    'name': 'test',
    'db': ads.dbPgsql({'database':env.PG_DWH_DB, 'user':env.PG_DWH_USER, 'password':env.PG_DWH_PWD, 'port':env.PG_DWH_PORT
                    , 'host':env.PG_DWH_HOST}, logger),
    'table': 'demo_pipeline',
    'cols': ['tenantname', 'taille', 'unite', 'fichier']
}

# Premier pipeline
pipe = ads.pipeline({
    'tableau': source, # Le tableau qui sert de source
    'db_destinations': destination,
    'batch_size': 1 # Optionnel, 1000 par défaut
}, logger)

rejects = pipe.run()
print(f"{len(rejects)} rejet(s) : {rejects}")

logger.info("Fin de la démonstration")