# adstoolbox[files]
"""
FileHandler : transfert, filtres, checksum, attente de fichier.

Tous les appels utilisent des paramètres nommés, y compris quand ils
correspondent à la valeur par défaut : c'est plus verbeux mais chaque option
devient visible.
"""
import os

import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
ads.set_timer(state=True)
env = ads.Env(logger)

# ---------------------------------------------------------------------------
# 1. Instanciation
# ---------------------------------------------------------------------------
local_f = ads.FileHandler(
    logger=logger,
    fs_url=None,        # None => backend local ("file:///")
    fs_kwargs=None,     # credentials et options du backend
    batch_size=4,       # lit/écrit 4 octets à la fois (4 096 par défaut)
    retry_count=1,      # 1 => une seule tentative, pas de retry
    retry_delay=1.5,    # secondes entre deux tentatives (sans effet ici)
)

# set_retry_params permet de changer ces deux réglages après coup, par exemple
# pour durcir une opération précise sans recréer le FileHandler.
local_f.set_retry_params(
    retry_count=3,
    retry_delay=0.5,
)

print(local_f.list_dir(dir_path="file"))

# ---------------------------------------------------------------------------
# 2. Écriture et lecture
# ---------------------------------------------------------------------------
local_f.write_file(
    file_path="file/file_test.txt",
    content=["Lorem Ipsum", "\n", "dolor sit amet"],  # doit être un itérable
    mode="w",  # 'w' écrase, 'a' ajoute à la fin, 'x' échoue si le fichier existe
)

for chunk in local_f.read_file(
    file_path="file/file_test.txt",
    mode="rb",      # 'b' => contenu restitué en bytes
    encoding=None,  # ignoré en mode binaire ; "utf-8" en mode texte
):
    print(chunk)

# create_empty_file crée un fichier vide, ou TRONQUE le fichier existant.
# Pratique pour un fichier témoin ou un verrou ; destructeur par inadvertance.
local_f.create_empty_file(file_path="file/file_vide.txt")

# ---------------------------------------------------------------------------
# 3. Transfert pur
# ---------------------------------------------------------------------------
local_f.transfer_file(
    src_path="file/file_test.txt",
    dst_path="file/file_test_copy.txt",
    dst_file_handler=None,  # un autre FileHandler si la destination est ailleurs
    mode="w",               # 'a' non implémenté ici : lève NotImplementedError
    fastcheck=False,        # True/défaut : compare les tailles
                            # False : compare les checksums MD5
    transform=None,         # aucun filtre : copie à l'identique
)

# ---------------------------------------------------------------------------
# 4. Filtrer le contenu pendant le transfert : le paramètre transform
# ---------------------------------------------------------------------------
# transform est une fonction bytes -> bytes appliquée à chaque chunk pendant la
# copie. Le contenu est transformé au vol, sans fichier intermédiaire ni
# chargement complet en mémoire.


def en_majuscules(chunk: bytes) -> bytes:
    """Passe le contenu en majuscules."""
    return chunk.upper()


resultat = local_f.transfer_file(
    src_path="file/file_test.txt",
    dst_path="file/file_test_upper.txt",
    dst_file_handler=None,
    mode="w",
    fastcheck=True,
    transform=en_majuscules,
)

# ATTENTION, deux conséquences à connaître :
#
# 1. transfer_file renvoie None au lieu de True quand transform est fourni.
#    C'est logique : la vérification d'intégrité n'a plus de sens si le
#    contenu change volontairement. Ne testez donc pas `if transfer_file(...)`
#    sur un transfert filtré, il serait toujours faux.
logger.info(f"Retour avec transform : {resultat} (None attendu, pas True)")

# 2. Les logs le rappellent avec le message
#    "Rien ne se perd, rien ne se crée, tout se transforme."
#    si le fastcheck est laissé à True.

for chunk in local_f.read_file(file_path="file/file_test_upper.txt", mode="rb"):
    print(chunk)

# transform travaille sur des BYTES, pas des str : `chunk.upper()` fonctionne
# sur des bytes, mais toute logique nécessitant du texte doit décoder puis
# réencoder explicitement.


def remplacer_ipsum(chunk: bytes) -> bytes:
    """Remplace un mot, en décodant explicitement."""
    return chunk.decode("utf-8").replace("Ipsum", "IPSUM").encode("utf-8")


# PIÈGE MAJEUR : le filtre s'applique CHUNK PAR CHUNK, et un motif à cheval
# sur deux chunks passe inaperçu SANS ERREUR. Mesuré sur "Lorem Ipsum" :
#
#   batch_size=4        -> 'Lorem Ipsum'   le remplacement ne s'est pas fait
#   batch_size=1048576  -> 'Lorem IPSUM'   correct
#
# Pour un filtre sensible aux frontières (remplacement, regex multi-lignes),
# augmentez batch_size au-delà de la taille du fichier, ou passez par
# read_file/write_file en assemblant le contenu vous-même. Un `.upper()` n'est
# pas concerné : il agit octet par octet.
gros_lecteur = ads.FileHandler(logger=logger, batch_size=1_048_576)
gros_lecteur.transfer_file(
    src_path="file/file_test.txt",
    dst_path="file/file_test_replace.txt",
    mode="w",
    fastcheck=True,
    transform=remplacer_ipsum,
)

# Autres usages typiques de transform : compression (gzip.compress),
# chiffrement, changement d'encodage, anonymisation de colonnes CSV.

# ---------------------------------------------------------------------------
# 5. Écrire en récupérant le checksum
# ---------------------------------------------------------------------------
# write_with_checksum écrit ET renvoie le MD5 hexadécimal du contenu écrit,
# en un seul passage. Utile pour journaliser une empreinte sans relire le
# fichier. C'est ce que transfer_file utilise en interne quand fastcheck=False.
empreinte = local_f.write_with_checksum(
    file_path="file/file_checksum.txt",
    content=[b"contenu a empreindre"],  # bytes attendus ici
    mode="wb",
)
logger.info(f"MD5 du contenu écrit : {empreinte}")

# ---------------------------------------------------------------------------
# 6. Attendre l'arrivée d'un fichier
# ---------------------------------------------------------------------------
# wait_for_file interroge le répertoire jusqu'à retry tentatives espacées de
# delay secondes. Renvoie True dès que le fichier apparaît, False sinon.
# Indispensable pour un batch qui consomme un dépôt alimenté par un tiers.
trouve = local_f.wait_for_file(
    path="file",
    filename="file_test.txt",
    retry=3,      # None => reprend le retry_count du FileHandler
    delay=1,      # None => reprend le retry_delay du FileHandler
)
logger.info(f"Fichier attendu trouvé : {trouve}")

# Si le DOSSIER n'existe pas, wait_for_file lève FileNotFoundError au lieu de
# renvoyer False : c'est une erreur de configuration, pas une attente.
try:
    local_f.wait_for_file(path="dossier_inexistant", filename="x.txt", retry=1, delay=0)
except FileNotFoundError as e:
    logger.info(f"Dossier absent, exception attendue : {e}")

# ---------------------------------------------------------------------------
# 7. Ménage
# ---------------------------------------------------------------------------
for chemin in (
    "file/file_test_copy.txt",
    "file/file_test_upper.txt",
    "file/file_test_replace.txt",
    "file/file_checksum.txt",
    "file/file_vide.txt",
):
    local_f.remove_file(file_path=chemin)

# ---------------------------------------------------------------------------
# 8. Les autres backends
# ---------------------------------------------------------------------------
# Ci-dessous des exemples de configuration, non exécutés : ils demandent des
# accès réels. Seule l'URL et fs_kwargs changent ; toutes les méthodes vues
# plus haut fonctionnent à l'identique, transform y compris.
exit()

# Azure Blob Storage — extra `files` (paquet adlfs)
azure_f = ads.FileHandler(
    logger=logger,
    fs_url="az://conteneur/prefixe",
    fs_kwargs={
        "account_name": "ACCOUNT",
        "sas_token": "CLE_SAS",
    },
)

# FTP / SFTP — extra `files` (paquet paramiko pour sftp://)
ftp_f = ads.FileHandler(
    logger=logger,
    fs_url="ftp://serveur/chemin",
    fs_kwargs={
        "username": "user",
        "password": "pwd",
    },
)

# Partage SMB — extra `files` (paquet smbprotocol)
smb_f = ads.FileHandler(
    logger=logger,
    fs_url="smb://serveur/partage",
    fs_kwargs={
        "username": "user",
        "password": "pwd",
    },
)

# Transfert entre deux backends : c'est le rôle de dst_file_handler.
local_f.transfer_file(
    src_path="file/file_test.txt",
    dst_path="depot/file_test.txt",
    dst_file_handler=smb_f,   # source locale, destination SMB
    mode="w",
    fastcheck=True,
    transform=en_majuscules,
)