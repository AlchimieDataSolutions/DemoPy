# adstoolbox[files]
import utils
import os
import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
ads.set_timer(state=True)
env = ads.Env(logger)

local_f = ads.FileHandler(
    logger,
    fs_url=None,
    fs_kwargs=None,
    batch_size=4, # batch_size signifie que local_f va lire/écrire 4 octets à la fois (4 096 par défaut)
    retry_count=1, # retry_count signifie que chaque opération ne sera tentée qu'une seule fois (pas de retry)
    retry_delay=1.5, # retry_delay signifie que chaque tentative sera espacée de 2s (inutile ici)
)

print(local_f.list_dir("file")) # Liste les fichiers/dossiers à l'endroit indiqué

local_f.write_file(
    file_path="file/file_test.txt",
    content=["Lorem Ipsum", "\n"], # le contenu doit être un itérable
    mode="w", # 'w' écrase le contenu présent, 'a' l'ajoute à la fin et 'x' renvoie une erreur si le fichier existe déjà
)

for chunk in local_f.read_file(
    file_path="file/file_test.txt",
    mode='rb', # 'b' signifie qu'on va restituer le contenu en bytes
    encoding = None,
):
    print(chunk)

local_f.transfer_file(
    src_path="file/file_test.txt",
    dst_path = "file/file_test_copy.txt",
    dst_file_handler = None, # On peut fournir un autre FileHandler si le contexte est différent
    mode = "w",
    fastcheck = False, # à True/par défaut, compare les tailles du fichier original à celui copié
    # à False, génère le checksum via protocole MD5 pour les comparer
) # C'est un transfert pur, si on applique des filtre au contenu il faudra utiliser read_file et write_file

exit()

# FileHandler azure
azure_f = ads.FileHandler(
    logger,
    fs_url="az://url",
    fs_kwargs={
        "account_name": "ACCOUNT",
        "sas_token": "CLE SAS",
    },
)

# FileHandler FTP
ftp_f = ads.FileHandler(
    logger,
    fs_url="ftp://url",
    fs_kwargs={
        "username": "user",
        "password": "pwd"
    },
)

smb_f = ads.FileHandler(
    logger,
    fs_url="smb://url",
    fs_kwargs={
        "username": "user",
        "password": "pwd"
    },
)