# adstoolbox[git]
"""
GitHandler : clonage, mise à jour, environnement virtuel.

L'extra git installe GitPython et PyGithub, mais le binaire `git` doit AUSSI
être présent dans le PATH : GitPython l'appelle en sous-processus. Sans lui,
l'import du module échoue avec "Bad git executable".
"""
import os

import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
ads.set_timer(state=True)
env = ads.Env(logger=logger)

# ---------------------------------------------------------------------------
# 1. Paramètres
# ---------------------------------------------------------------------------
# Le token est un PAT GitHub avec accès au dépôt. Ne le mettez jamais en dur :
# il vient du .env.
token = env.GITHUB_TOKEN
repo = f"AlchimieDataSolutions/{env.get(item='GITHUB_REPO', default='DemoPy')}"
branch = env.get(item="GITHUB_BRANCH", default=None)

# La destination doit soit ne pas exister, soit être DÉJÀ un dépôt git (avec
# un .git dedans). Un dossier vide existant ne fonctionne pas : c'est la
# commande de clonage qui doit créer le dossier.
destination = os.path.join(os.path.expanduser("~"), "demo_git_target")

gh = ads.GitHandler(
    token=token,
    logger=logger,
)

# ---------------------------------------------------------------------------
# 2. Vérifier les permissions avant d'agir
# ---------------------------------------------------------------------------
# check_permissions teste l'accès en LECTURE (os.R_OK) sur le chemin et lève
# PermissionError sinon. À appeler avant clone_or_update sur un chemin réseau
# ou un montage, pour échouer tôt avec un message clair plutôt qu'au milieu
# d'un clonage.
#
# Attention : il ne teste que la lecture, pas l'écriture. Un dossier lisible
# mais non inscriptible passera cette vérification et échouera plus tard.
try:
    gh.check_permissions(path=os.path.expanduser("~"))
    logger.info("Permissions de lecture confirmées.")
except PermissionError as e:
    logger.error(message=f"Permissions insuffisantes : {e}")

# Sur un chemin inexistant, os.access renvoie False : l'erreur porte donc sur
# les permissions alors que le vrai problème est l'absence du chemin.
try:
    gh.check_permissions(path="/chemin/qui/nexiste/pas")
except PermissionError as e:
    logger.warning(message=f"Chemin absent, signalé comme permission : {e}")

# ---------------------------------------------------------------------------
# 3. Cloner ou mettre à jour
# ---------------------------------------------------------------------------
# Si le dépôt n'existe pas localement, il est cloné. S'il existe, un pull est
# fait sur la branche demandée. C'est la même méthode dans les deux cas, d'où
# son nom.
gh.clone_or_update(
    destination_path=destination,
    repository=repo,          # "organisation/depot", pas une URL complète
    branch=branch,            # None => branche par défaut du dépôt
)

# ---------------------------------------------------------------------------
# 4. Préparer l'environnement virtuel du dépôt cloné
# ---------------------------------------------------------------------------
# setup_virtualenv crée un venv dans le dépôt, puis :
#   - si un requirements.txt est présent, installe les dépendances dedans ;
#     sinon, émet un warning et continue ;
#   - si un launch.sh est présent, lui attribue les droits d'exécution (755).
#
# Le requirements.txt en question est celui du dépôt CLONÉ, pas celui
# d'adsToolBox.
gh.setup_virtualenv(
    repo_path=destination,
)

logger.info("Dépôt prêt.")