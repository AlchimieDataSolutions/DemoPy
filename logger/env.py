import os
import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
env = ads.env(logger, file=None)
# Vous pouvez spécifier le chemin absolu du fichier env ou le mettre avec le fichier à exécuter
# Sinon ads.env cherchera un .env en remontant à partir du fichier appelant

# Les variables d'environnement sont maintenant accessibles comme cela
print(env.PG_DWH_DB)