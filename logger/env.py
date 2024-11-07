from CommonLib import *

logger = ads.Logger(None, ads.Logger.DEBUG, "AdsLogger")

env = ads.env(logger)
# Vous pouvez spécifier le chemin absolu du fichier env ou le mettre avec le fichier à exécuter

# Les variables d'environnement sont maintenant accessibles comme cela
print(env.PG_DWH_DB)