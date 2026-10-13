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
# 6. Cas particulier : machine au jeu d'instructions ancien
# ---------------------------------------------------------------------------
# Polars ne contient pas son moteur de calcul : il le charge depuis un paquet
# de runtime séparé, compilé pour un jeu d'instructions récent. Sur une
# machine qui ne le gère pas, l'import avertit puis le processus plante.
#
# La parade est d'installer le runtime de compatibilité :
#
#   pip install "adstoolbox[pgsql]"
#   pip install "polars[rtcompat]"
#
# ATTENTION si vous avez connu l'ancienne méthode, basée sur polars-lts-cpu :
# cette distribution est figée à la version 1.33.1 et fournit un module
# `polars` CONCURRENT, qui s'écrase avec le paquet officiel. Désinstallez-la
# avant de passer à rtcompat, et ne déclarez jamais les deux dans un même
# requirements.txt.
#
# polars[rtcompat] n'a pas ce défaut : il ajoute un paquet de runtime à côté
# de polars, sans le remplacer, et suit ses versions.

# ---------------------------------------------------------------------------
# 7. Un prérequis que les extras ne couvrent pas : pgcrypto
# ---------------------------------------------------------------------------
# Les extras installent des paquets Python. Ils ne peuvent rien pour ce que la
# BASE doit fournir de son côté.
#
# Le CDC calcule son empreinte de clé avec digest(), fourni par l'extension
# PostgreSQL pgcrypto, absente d'une installation nue. ChangeDataCapture le
# vérifie au démarrage et indique la commande à passer :
#
#   CREATE EXTENSION pgcrypto;
#
# L'empreinte de ligne, elle, utilise md5() qui est natif : seul SHA2-256
# impose l'extension. SQL Server n'est pas concerné, il passe par HASHBYTES.
# Sur une base managée, l'activation demande souvent des droits
# d'administration : à anticiper avant la mise en production.

logger.info("Fin de la démonstration du modèle d'installation.")