# adstoolbox[git]
import os
import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
ads.set_timer(state=True)
env = ads.Env(logger)

token = env.GITHUB_TOKEN
repo = f"AlchimieDataSolutions/{getattr(env, 'GITHUB_REPO', None)}"
branch = env.GITHUB_BRANCH if hasattr(env, 'GITHUB_BRANCH') else None

# Attention, la destination est déjà un repo avec un .git dedans ou alors n'existe pas
# Si le dossier cible est un dossier vide, ça ne fonctionnera pas, la commande doit créer le dossier
destination = r"C:\Users\mvann\Desktop\ADS\Projects\TEST"

gh = ads.GitHandler(token, logger)

# Si le dépot n'existe pas, il sera crée
# S'il existe, on fait un pull sur la branche choisie
gh.clone_or_update(destination, repo, branch)

# Installe les dépendances du requirements.txt et attribue les droits au fichier launch.sh si celui-ci existe
gh.setup_virtualenv(destination)