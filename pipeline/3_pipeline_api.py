from get_api_data import *
from CommonLib import *


monAPI=NxOnyxApi(domain=env.ORISHA_PROD_TENANTDOMAIN,username=env.ORISHA_PROD_TENANTUSERNAME,password=env.ORISHA_PROD_TENANTPASSWORD,tenantId=env.ORISHA_PROD_TENANTID)
data=monAPI.getTree()


# Extraire la liste des clés
noms_cles = list(data[0].keys())

# Extraire la liste des valeurs sous forme de tuples
valeurs_tuples = [tuple(d.values()) for d in data]

logger.info("Noms des clés : "+ str(noms_cles))
logger.info("Valeurs sous forme de tuples : "+ str(valeurs_tuples))


destination = {
    'name': 'test',
    'db': ads.dbPgsql({'database':env.PG_DWH_DB, 'user':env.PG_DWH_USER, 'password':env.PG_DWH_PWD, 'port':env.PG_DWH_PORT
                    , 'host':env.PG_DWH_HOST}, logger),
    'table': 'demo_pipeline',
    'cols': ['id', 'categoryId', 'name', 'isExpanded']
}


pipeline = ads.pipeline({'tableau': valeurs_tuples, 'db_destination': destination, 'table': 'onyx_qs.test',
                 'cols': noms_cles}, logger)

pipeline.run()
logger.info("Fin de la démonstration")