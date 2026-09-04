# adstoolbox[mssql,mysql,pgsql]
"""
Connexions aux trois bases : cycle de vie et paramètres.

Ce script se limite au cycle de vie d'une connexion et aux clés attendues
par chaque backend. Pour l'interface commune (sql_query, insert, upsert...)
et ce qui reste spécifique à chaque SGBD, voir operations/polymorphisme.py.
"""
import os

import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
env = ads.Env(logger=logger)

# ---------------------------------------------------------------------------
# 1. Les clés du dictionnaire de connexion
# ---------------------------------------------------------------------------
# Les trois backends lisent les MÊMES cinq clés, via dictionnary.get() :
#   database, user, password, port, host
#
# Conséquence du .get() : une clé absente ou mal orthographiée ne lève PAS
# d'erreur à l'instanciation. Elle vaut None, et l'échec n'apparaît qu'à
# connect(), avec un message venant du driver. Vérifiez vos noms de clés.
#
# batch_size est le troisième argument, pas une clé du dictionnaire. Il fixe
# le nombre de lignes par itération en lecture comme en écriture.

# ---------------------------------------------------------------------------
# 2. PostgreSQL
# ---------------------------------------------------------------------------
source_pg = ads.DbPgsql(
    {
        "database": env.PG_DWH_DB,
        "user": env.PG_DWH_USER,
        "password": env.PG_DWH_PWD,
        "port": env.PG_DWH_PORT,
        "host": env.PG_DWH_HOST,
    },
    logger=logger,
    batch_size=1,   # 1 pour observer les batchs ; 10 000 par défaut
)

# connect() est indispensable : l'instanciation ne connecte rien.
source_pg.connect()

# disconnect() ferme la connexion ET remet self.connection à None. À appeler
# dans un finally si le traitement peut lever, sinon la connexion reste
# ouverte côté serveur jusqu'au timeout.
source_pg.disconnect()

# PIÈGE : disconnect() commence par appeler _check_connection(). Comme
# connection vaut None après une première fermeture, un SECOND disconnect()
# rouvre la connexion avant de la refermer aussitôt. Inoffensif mais
# coûteux — un aller-retour réseau complet pour rien. Ne fermez qu'une fois,
# ou testez `if source_pg.connection:` avant.

# ---------------------------------------------------------------------------
# 3. SQL Server : la clé charset en plus
# ---------------------------------------------------------------------------
# DbMssql accepte une sixième clé, charset, qui vaut "UTF-8" par défaut et
# est passée telle quelle à pymssql. La renseigner n'est utile que face à
# une base dans un encodage ancien (latin1, cp1252).
source_mssql = ads.DbMssql(
    {
        "database": env.MSSQL_DWH_DB,
        "user": env.MSSQL_DWH_USER,
        "password": env.MSSQL_DWH_PWD,
        "port": env.MSSQL_DWH_PORT,
        "host": env.MSSQL_DWH_HOST,
        "charset": "UTF-8",   # défaut, explicité ici pour mémoire
    },
    logger=logger,
    batch_size=1,
)
source_mssql.connect()
source_mssql.disconnect()

# ---------------------------------------------------------------------------
# 4. MySQL
# ---------------------------------------------------------------------------
source_mysql = ads.DbMysql(
    {
        "database": env.MYSQL_DWH_DB,
        "user": env.MYSQL_DWH_USER,
        "password": env.MYSQL_DWH_PWD,
        "port": env.MYSQL_DWH_PORT,
        "host": env.MYSQL_DWH_HOST,
    },
    logger=logger,
    batch_size=1,
)
source_mysql.connect()
source_mysql.disconnect()

# ---------------------------------------------------------------------------
# 5. Reconnexion implicite, et ses limites
# ---------------------------------------------------------------------------
# Toute méthode d'exécution appelle _check_connection() en amont. Si
# self.connection est None, connect() est rappelé automatiquement : après un
# disconnect(), une requête se reconnecte donc toute seule.
source_pg.connect()
source_pg.disconnect()
resultat = source_pg.sql_scalaire(query="SELECT 1")   # reconnecte au passage
logger.info(f"Reconnexion implicite après disconnect : {resultat}")

# ATTENTION à la portée exacte de ce mécanisme. Le test est
# `if not self.connection`, donc il ne détecte que le cas où la connexion
# est None. Une connexion COUPÉE côté serveur (timeout, redémarrage,
# coupure réseau) reste un objet non-None : le test passe, la requête part
# sur une connexion morte et échoue.
#
# Les classes Db* n'ont ni retry_count ni retry_delay et n'utilisent pas
# retry_on_failure — contrairement à FileHandler. Pour un traitement long
# ou fragile, gérez vous-même la reprise : voir logger/retry.py, section 4,
# qui montre comment décorer votre propre méthode.

# ---------------------------------------------------------------------------
# 6. Le logger reçoit la connexion
# ---------------------------------------------------------------------------
# Une instance Db* peut alimenter les tables de logs. set_connection accepte
# soit l'objet ads (il en extrait .connection), soit une connexion driver
# brute. Voir logger/logger.py pour le détail.
logger.set_connection(ads_connection=source_pg, log_level=ads.Logger.INFO)
logger.info("Ce message part aussi dans LOGS_details.")
logger.log_close(status="SUCCESS", message="Démonstration des connexions terminée")

source_pg.disconnect()