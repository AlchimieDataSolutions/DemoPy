# adstoolbox[files]
import utils
import os
import threading
import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
env = ads.Env(logger)

local_f = ads.FileHandler(
    logger,
    fs_url=None,
    fs_kwargs=None,
    batch_size=4, # batch_size signifie que local_f va lire/écrire 4 octets à la fois (4 096 par défaut)
    retry_count=1, # retry_count signifie que chaque opération ne sera tentée qu'une seule fois (pas de retry)
    retry_delay=1.5, # retry_delay signifie que chaque tentative sera espacée de 2s (inutile ici)
)

if local_f.file_exists("file/file.txt"):
    local_f.remove_file("file/file.txt")

print(f"Le fichier 'file/file.txt' existe: {local_f.file_exists('file/file.txt')}")
print(f"Le dossier 'file' existe: {local_f.directory_exists('file')}") # Vérifie si un dossier existe

# Lister les fichier du répertoire
print(os.listdir("file"))

############################################################################

# On va simuler la réception/création d'un fichier après 3 secondes
def create_file_with_delay(fh, file_path, delay, logger):
    import time
    logger.info(f"Création du fichier dans {delay} secondes...")
    time.sleep(delay)
    fh.write_file(file_path, "content", "w")
    logger.info(f"Fichier créé.")

if local_f.file_exists("file/test.txt"): local_f.remove_file("file/test.txt")
threading.Thread(target=create_file_with_delay, args=(local_f, "file/test.txt", 3, logger)).start()

if local_f.wait_for_file(os.getcwd(), "file/test.txt", 5):
    logger.info("Fichier bien trouvé")
else:
    logger.error("Pas de fichier trouvé")

############################################################################

# Instanciation d'une connexion à une base PostgreSQL (adstoolbox[pgsql])
source = ads.DbPgsql({'database':env.PG_DWH_DB
                    , 'user':env.PG_DWH_USER
                    , 'password':env.PG_DWH_PWD
                    , 'port':env.PG_DWH_PORT
                    , 'host':env.PG_DWH_HOST}, logger, 10)

# Scanne les fichiers selon le filter à partir de base_path et insère en base le résultat (taille, occurrences)
local_f.disk_check(
    db=source,
    schema="",
    table="disk_check",
    base_path=os.getcwd(), # Répertoire de départ
    file_filter=".txt", # Filtre les fichiers à analyser
)