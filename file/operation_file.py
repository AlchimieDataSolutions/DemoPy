# adstoolbox[files]
# adstoolbox[pgsql]  pour la section 4 (disk_check) seulement
"""
FileHandler : existence, listage, attente, inventaire disque.

Pour le transfert, les filtres transform et les checksums, voir
file/transfer_file.py.
"""
import os
import threading
import time

import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
env = ads.Env(logger=logger)

local_f = ads.FileHandler(
    logger=logger,
    fs_url=None,        # None => backend local ("file:///")
    fs_kwargs=None,
    batch_size=4,       # 4 octets à la fois ; 4 096 par défaut
    retry_count=1,      # 1 => une seule tentative, pas de retry
    retry_delay=1.5,    # secondes entre deux tentatives
)

# ---------------------------------------------------------------------------
# 1. Tester l'existence
# ---------------------------------------------------------------------------
# Deux méthodes distinctes, et la distinction compte : file_exists vérifie
# l'existence ET qu'il s'agit bien d'un fichier, directory_exists fait de
# même pour un dossier. Un chemin de dossier passé à file_exists renvoie
# donc False, pas une erreur.
if local_f.file_exists(file_path="file/file.txt"):
    local_f.remove_file(file_path="file/file.txt")

print(f"'file/file.txt' existe : {local_f.file_exists(file_path='file/file.txt')}")
print(f"'file' est un dossier  : {local_f.directory_exists(dir_path='file')}")
print(f"'file' vu par file_exists : {local_f.file_exists(file_path='file')}")

# remove_file renvoie un booléen et NE LÈVE PAS d'erreur sur un fichier
# absent : il journalise un warning et renvoie False. Utile pour un ménage
# idempotent, trompeur si vous attendiez une exception.
print(f"Suppression d'un fichier absent : {local_f.remove_file(file_path='file/inexistant.txt')}")

# ---------------------------------------------------------------------------
# 2. Lister un répertoire
# ---------------------------------------------------------------------------
# list_dir renvoie les NOMS de base, pas les chemins complets — contrairement
# au fs.ls() de fsspec qu'il encapsule. Il fonctionne sur tous les backends,
# là où os.listdir ne connaît que le disque local.
print(local_f.list_dir(dir_path="file"))

# list_dir n'est pas récursif. Pour parcourir une arborescence, c'est
# disk_check qui s'en charge (section 4), ou fs.ls() en direct.

# ---------------------------------------------------------------------------
# 3. Attendre l'arrivée d'un fichier
# ---------------------------------------------------------------------------
# Cas réel : un tiers dépose un fichier et le traitement doit patienter.
# On simule le dépôt dans un thread, trois secondes plus tard.
def create_file_with_delay(fh: ads.FileHandler, file_path: str, delay: float,
                           logger: ads.Logger) -> None:
    """Crée un fichier après un délai, pour simuler un dépôt externe."""
    logger.info(message=f"Création du fichier dans {delay} secondes...")
    time.sleep(delay)
    # content doit être un ITÉRABLE : une chaîne nue serait parcourue
    # caractère par caractère, ce qui fonctionne mais écrit lettre à lettre.
    fh.write_file(file_path=file_path, content=["content"], mode="w")
    logger.info(message="Fichier créé.")


if local_f.file_exists(file_path="file/test.txt"):
    local_f.remove_file(file_path="file/test.txt")

threading.Thread(
    target=create_file_with_delay,
    args=(local_f, "file/test.txt", 3, logger),
).start()

# ATTENTION à la découpe des arguments : wait_for_file assemble lui-même
# f"{path}/{filename}". Le dossier va dans `path`, le seul nom de fichier
# dans `filename`. Mettre "file/test.txt" dans filename fonctionne par
# accident, mais le message d'erreur devient trompeur et la vérification
# d'existence du dossier porte sur le mauvais chemin.
trouve = local_f.wait_for_file(
    path="file",
    filename="test.txt",
    retry=5,       # None => reprend le retry_count du FileHandler
    delay=1,       # None => reprend le retry_delay du FileHandler
)

if trouve:
    logger.info(message="Fichier bien trouvé")
else:
    logger.error(message="Pas de fichier trouvé")

# retry × delay doit couvrir le délai réel d'arrivée : ici 5 × 1 s pour un
# dépôt à 3 s. Trop court, la méthode renvoie False alors que le fichier
# finira par arriver.
#
# Et si le DOSSIER n'existe pas, wait_for_file lève FileNotFoundError au
# lieu de renvoyer False : c'est une erreur de configuration, pas une
# attente légitime.
try:
    local_f.wait_for_file(path="dossier_absent", filename="x.txt", retry=1, delay=0)
except FileNotFoundError as e:
    logger.info(message=f"Dossier absent : {e}")

local_f.remove_file(file_path="file/test.txt")

# ---------------------------------------------------------------------------
# 4. disk_check : inventorier une arborescence en base
# ---------------------------------------------------------------------------
# adstoolbox[pgsql] à partir d'ici.
#
# Parcourt base_path RÉCURSIVEMENT, retient les fichiers dont le nom
# contient file_filter, et insère une ligne par fichier dans la table cible
# (tenant, date, taille, unité, chemin) plus une ligne de TOTAL.
source = ads.DbPgsql(
    {
        "database": env.PG_DWH_DB,
        "user": env.PG_DWH_USER,
        "password": env.PG_DWH_PWD,
        "port": env.PG_DWH_PORT,
        "host": env.PG_DWH_HOST,
    },
    logger=logger,
    batch_size=10,
)

local_f.disk_check(
    db=source,
    schema="",
    table="disk_check",
    base_path=os.getcwd(),   # départ du parcours
    tenant_name="DEFAULT",   # libellé écrit dans chaque ligne
    file_filter=".txt",      # sous-chaîne recherchée dans le chemin
)

# Quatre points à connaître :
#
# 1. file_filter est une simple SOUS-CHAÎNE, pas un motif glob ni une regex.
#    ".txt" retient aussi "notes.txt.bak" et "txt_archive/donnees.csv".
#
# 2. La table est créée automatiquement si elle n'existe pas, avec le type
#    de date adapté au backend (TIMESTAMP pour Postgres et MySQL, DATETIME2
#    pour SQL Server). Une base d'un autre type lève un TypeError.
#
# 3. Aucun fichier trouvé n'est pas une erreur : un warning est journalisé
#    et la méthode s'arrête sans rien insérer, sans ligne de total.
#
# 4. base_path=os.getcwd() parcourt tout le dépôt, y compris venv/ et .git/
#    s'ils sont là. Ciblez un sous-dossier pour un inventaire utile.
#
# Les tailles sont converties en unité lisible (octets, Ko, Mo, Go, To) et
# stockées avec leur unité dans une colonne séparée — donc pas directement
# sommables en SQL. Pour cumuler, il faut reconvertir.

source.disconnect()