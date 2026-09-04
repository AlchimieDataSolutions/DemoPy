"""
Modèle d'installation : cœur, extras et chargement paresseux.

Ce script est le seul du dépôt qui tourne avec `pip install adstoolbox` nu,
sans aucun extra. Il illustre ce que l'installation de base fournit, ce
qu'elle ne fournit pas, et comment adsToolBox le signale.
"""
import os

import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")

# ---------------------------------------------------------------------------
# 1. Le cœur : disponible sans aucun extra
# ---------------------------------------------------------------------------
# `pip install adstoolbox` installe seulement requests, chardet, python-dotenv
# et tzdata (Windows). Environ 20 Mo. Cela suffit pour :
#   Logger, Env, MailReader, OdooConnector,
#   timer, get_timer, set_timer, now, set_timezone,
#   retry_on_failure, get_public_ip
logger.info("Le logger fonctionne sans aucun extra.")

# ---------------------------------------------------------------------------
# 2. Chargement paresseux (PEP 562)
# ---------------------------------------------------------------------------
# `import adsToolBox` n'importe AUCUNE dépendance tierce. Chaque module est
# chargé au premier accès à l'un de ses symboles. Conséquence pratique :
# l'import du package ne casse jamais, même si polars ou psycopg2 manquent.
import sys  # noqa: E402

tierces = {"polars", "psycopg2", "pymssql", "pymysql", "fsspec", "git", "github"}
chargees = sorted(tierces & {m.split(".")[0] for m in sys.modules})
logger.info(f"Dépendances tierces chargées par `import adsToolBox` : {chargees or 'aucune'}")

# Corollaire : le coût d'un `import adsToolBox` est constant, quel que soit le
# nombre d'extras installés. Inutile de faire des imports sélectifs pour la
# performance ; `import adsToolBox as ads` suffit.

# ---------------------------------------------------------------------------
# 3. Ce qui demande un extra, et comment l'erreur le dit
# ---------------------------------------------------------------------------
# L'erreur ne survient pas à l'import du package mais au premier usage du
# symbole, et elle nomme l'extra à installer.
attendus = {
    "DataFactory": "dataframe",
    "Pipeline": "dataframe",
    "DataComparator": "dataframe",
    "DbMssql": "mssql",
    "DbMysql": "mysql",
    "DbPgsql": "pgsql",
    "FileHandler": "files",
    "GitHandler": "git",
    "GoogleCalendarConnector": "google",
    "ChangeDataCapture": "cdc",
}

disponibles, manquants = [], []
for symbole, extra in attendus.items():
    try:
        getattr(ads, symbole)
    except ImportError:
        # Le message complet ressemble à :
        #   DbPgsql requiert une dépendance non installée (No module named
        #   'psycopg2'). Installez-la avec : pip install "adstoolbox[pgsql]".
        manquants.append(f"{symbole} -> adstoolbox[{extra}]")
    else:
        disponibles.append(symbole)

logger.info(f"Symboles disponibles ici : {', '.join(disponibles) or 'aucun'}")
for m in manquants:
    logger.warning(f"Indisponible : {m}")

# ---------------------------------------------------------------------------
# 4. Choisir ses extras
# ---------------------------------------------------------------------------
# pip install "adstoolbox[pgsql]"               PostgreSQL (+ polars)
# pip install "adstoolbox[mssql,mysql,pgsql]"   les trois bases
# pip install "adstoolbox[files]"               FileHandler
# pip install "adstoolbox[all]"                 tout, environ 480 Mo
#
# Les guillemets sont nécessaires sous zsh, qui interprète les crochets.
#
# Les extras de base incluent polars, donc [pgsql] est autosuffisant : pas
# besoin d'ajouter [dataframe] pour utiliser Pipeline avec une base.
#
# ATTENTION : un extra qui n'existe pas ne provoque PAS d'erreur, seulement
# un avertissement, et rien n'est installé :
#
#   $ pip install "adstoolbox[pymssql]"
#   WARNING: adstoolbox 2026.9.2 does not provide the extra 'pymssql'
#
# Le nom correct est `mssql`, pas `pymssql`. Les neuf extras valides sont :
# dataframe, mssql, mysql, pgsql, files, git, google, cdc, all.

# ---------------------------------------------------------------------------
# 5. Vérifier ce dont un script a besoin
# ---------------------------------------------------------------------------
# Chaque script de ce dépôt porte en commentaire l'extra qu'il exige, par
# exemple `# adstoolbox[pgsql]`. Le tableau du README fait la synthèse.

# ---------------------------------------------------------------------------
# 6. Cas particulier : processeur sans AVX2
# ---------------------------------------------------------------------------
# adsToolBox dépend de `polars`, le build standard, qui exige AVX2. Sur une
# machine plus ancienne, il faut basculer APRÈS l'installation :
#
#   pip install "adstoolbox[pgsql]"
#   pip install --force-reinstall --no-deps polars-lts-cpu
#
# --force-reinstall est indispensable : les deux distributions fournissent le
# même module `polars` sans se déclarer incompatibles, donc pip considère la
# contrainte satisfaite et ne remplace pas les fichiers. Ne jamais déclarer
# les deux dans un même requirements.txt : elles s'écrasent mutuellement et
# `import polars` devient inutilisable.

logger.info("Fin de la démonstration du modèle d'installation.")