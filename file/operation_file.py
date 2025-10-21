import os
import threading
import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
env = ads.env(logger)

fh = ads.FileHandler(logger, batch_size=20)

if fh.file_exists('file/file.txt'): # Vérifie si un fichier existe
    fh.remove_file("file/file.txt") # Supprime un fichier

print(f"Le fichier 'file/file.txt' existe: {fh.file_exists('file/file.txt')}")
print(f"Le dossier 'file' existe: {fh.directory_exists('file')}") # Vérifie si un dossier existe

content = [b"ligne1\n", b"ligne2\n"]
fh.write_file("file/file.txt", content, mode="wb") # Vide le fichier et écrit en binaire
print(f"Le fichier 'file/file.txt' existe: {fh.file_exists('file/file.txt')}") # Devrait être vrai maintenant

content = ["ligne3\n", "ligne4", "ligne5"]
fh.write_file("file/file.txt", content, mode="a") # Écrit à la suite dans un fichier

# Lister les fichier du répertoire
print(os.listdir("file"))

# Lit un fichier batch par batch
for num_batch, chunk in enumerate(fh.read_file("file/file.txt", mode="r", encoding="utf-8"), start=1):
    print(f"Batch {num_batch}: \n{chunk}")

############################################################################

# On va simuler la réception/création d'un fichier après 3 secondes
def create_file_with_delay(fh, file_path, delay, logger):
    import time
    logger.info(f"Création du fichier dans {delay} secondes...")
    time.sleep(delay)
    fh.write_file(file_path, "content", "w")
    logger.info(f"Fichier créé.")

if fh.file_exists("file/test.txt"): fh.remove_file("file/test.txt")
threading.Thread(target=create_file_with_delay, args=(fh, "file/test.txt", 2, logger)).start()

if fh.wait_for_file(os.getcwd(), "file/test.txt", 10):
    logger.info("Fichier bien trouvé")
else:
    logger.error("Pas de fichier trouvé")

############################################################################

# Toutes ces opérations ont un équivalent via un protocole SMB, si le FileHandler est défini comme suit

smb_config = {
    "server": "MON_SERVEUR",
    "username": "user",
    "password": "pwd"
}

# Attention, la déclaration lance une tentative de connexion
# fh_smb = ads.FileHandler(logger, smb_config)

############################################################################

# Instanciation d'une connexion à une base PostgreSQL
source = ads.dbPgsql({'database':env.PG_DWH_DB
                    , 'user':env.PG_DWH_USER
                    , 'password':env.PG_DWH_PWD
                    , 'port':env.PG_DWH_PORT
                    , 'host':env.PG_DWH_HOST}, logger, 10)

# Scan les fichiers selon le filter à partir de base_path et insère en base le résultat
fh.disk_check(source, schema="", table="disk_check", base_path=os.getcwd(), filter='.txt')