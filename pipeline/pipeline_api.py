import os
from uuid import uuid4
import adsToolBox as ads
from get_api_data import *
from datetime import datetime, date, time

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
ads.set_timer(True)
env = ads.env(logger)

# Cette démonstration est très similaire au pipeline_tableau, le tableau vient simplement d'une api

api = NxOnyxApi(
    domain=env.API_DOMAIN,
    username=env.API_USER,
    password=env.API_PASSWORD,
    tenantId=env.TENANT_ID
)

data = api.getTree()

# Extraire la liste des clés
noms_cles = list(data[0].keys())

# Extraire la liste des valeurs sous forme de tuples
valeurs_tuples = [tuple(d.values()) for d in data]

logger.info("Noms des clés : "+ str(noms_cles))
logger.info("Valeurs sous forme de tuples : "+ str(valeurs_tuples))

db = ads.dbPgsql({
    'database':env.PG_DWH_DB,
    'user':env.PG_DWH_USER,
    'password':env.PG_DWH_PWD,
    'port':env.PG_DWH_PORT,
    'host':env.PG_DWH_HOST}
, logger)

destination = {
    'name': 'test',
    'db': db,
    'table': 'demo_pipeline',
    'cols': ['id', 'categoryId', 'name', 'isExpanded']
}

pipeline = ads.pipeline({'tableau': valeurs_tuples, 'db_destination': destination, 'table': 'onyx_qs.test',
                 'cols': noms_cles}, logger)

print(pipeline.run())