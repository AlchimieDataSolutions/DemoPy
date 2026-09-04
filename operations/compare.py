# adstoolbox[mysql,pgsql]
"""
DataComparator : comparer deux sources batch par batch.

PRÉREQUIS : les deux bases doivent contenir la table insert_test avec les
mêmes données. Lancez d'abord `python pipeline/pipeline.py`, qui remplit
MySQL puis recopie vers PostgreSQL.

L'ancienne version de ce script importait pipeline.pipeline pour provoquer
ce remplissage. C'était fragile : l'import exécutait tout le script en
effet de bord, dépendait de ses noms de variables internes, et empêchait de
lancer la comparaison seule. Les connexions sont désormais déclarées ici.
"""
import os

import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
ads.set_timer(state=True)
env = ads.Env(logger=logger)

table = "insert_test"

source_pg = ads.DbPgsql(
    {
        "database": env.PG_DWH_DB,
        "user": env.PG_DWH_USER,
        "password": env.PG_DWH_PWD,
        "port": env.PG_DWH_PORT,
        "host": env.PG_DWH_HOST,
    },
    logger=logger,
)
source_mysql = ads.DbMysql(
    {
        "database": env.MYSQL_DWH_DB,
        "user": env.MYSQL_DWH_USER,
        "password": env.MYSQL_DWH_PWD,
        "port": env.MYSQL_DWH_PORT,
        "host": env.MYSQL_DWH_HOST,
    },
    logger=logger,
)

# ---------------------------------------------------------------------------
# 1. Adapter les requêtes, pas les données
# ---------------------------------------------------------------------------
# C'est tout l'enjeu de ce script. Les données sont IDENTIQUES dans les deux
# bases, mais chaque backend les restitue à sa façon. Sans adaptation, la
# comparaison échoue sur des différences de représentation, pas de contenu.
#
# Les écarts traités ci-dessous :
#   NUMERIC     Postgres affiche des zéros de fin, MySQL non
#               -> TO_CHAR côté Postgres, CAST AS CHAR côté MySQL
#   TIME        MySQL renvoie une durée illisible pour Polars
#               -> TO_CHAR / TIME_FORMAT des deux côtés
#   BOOLEAN     Postgres renvoie true/false, MySQL 1/0
#               -> CAST AS INT côté Postgres
#   CHAR(n)     Postgres complète par des espaces jusqu'à n, MySQL non
#               -> TRIM TRAILING côté Postgres
#
# ORDER BY est indispensable des deux côtés : la comparaison est
# POSITIONNELLE, batch par batch. Sans tri garanti, deux bases contenant
# exactement les mêmes lignes seraient déclarées différentes.
query_pg = f"""
SELECT id_int, name_varchar, description_text, count_int, id_bigint,
       TO_CHAR(amount_numeric, 'FM9999999990.000') AS amount_numeric,
       ratio_double, score_real, created_date, created_at, updated_at,
       TO_CHAR(event_time, 'HH24:MI:SS') AS event_time,
       CAST(is_active AS INT), uuid_key,
       TRIM(TRAILING FROM code_char) AS code_char
FROM {table} ORDER BY 1
"""
query_mysql = f"""
SELECT id_int, name_varchar, description_text, count_int, id_bigint,
       CAST(amount_numeric AS CHAR) AS amount_numeric,
       ratio_double, score_real, created_date, created_at, updated_at,
       TIME_FORMAT(event_time, '%H:%i:%s') AS event_time,
       is_active, uuid_key, code_char
FROM {table} ORDER BY 1
"""

# Les colonnes doivent être dans le MÊME ORDRE et en même nombre des deux
# côtés. Ici price_numeric est volontairement absente des deux requêtes :
# omettre une colonne d'un seul côté suffirait à tout faire échouer.

# ---------------------------------------------------------------------------
# 2. Configuration
# ---------------------------------------------------------------------------
# Cinq clés, toutes lues via .get(). Il n'y a pas de db_destination : les
# deux sources sont symétriques, aucune n'est la référence.
dc = ads.DataComparator(
    {
        "db_source_1": source_pg,
        "db_source_2": source_mysql,
        "query_source_1": query_pg,
        "query_source_2": query_mysql,
        "batch_size": 10_000,   # défaut 10 000
    },
    logger=logger,
)

# ---------------------------------------------------------------------------
# 3. compare
# ---------------------------------------------------------------------------
# Renvoie un booléen. check_dtypes=True compare aussi les TYPES Polars des
# colonnes, pas seulement les valeurs : c'est le mode strict, et c'est lui
# qui révèle les écarts de représentation entre backends.
#
# check_dtypes=False (défaut) tolère qu'une colonne soit Int64 d'un côté et
# String de l'autre tant que les valeurs se correspondent — utile pour un
# premier diagnostic sur des bases hétérogènes.
identiques = dc.compare(check_dtypes=True)

logger.info(f"Les deux sources sont identiques : {identiques}")

# compare renvoie False dès la PREMIÈRE différence rencontrée et s'arrête :
# ce n'est pas un rapport exhaustif des écarts, mais un test d'égalité. Le
# détail de la différence est journalisé.
#
# Il renvoie également False si une source se termine avant l'autre — cas
# d'un nombre de lignes différent.
#
# Sur de gros volumes, les DataFrames affichés dans les logs deviennent
# illisibles : réduisez batch_size pour un diagnostic, ou restreignez les
# requêtes à quelques colonnes suspectes.

if not identiques:
    logger.warning("Consultez les logs ci-dessus pour le batch en écart.")

source_pg.disconnect()
source_mysql.disconnect()