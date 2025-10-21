# Cet import va lancer le script pipeline.pipeline qui met dans deux bases (une Postgre et une dbMysql) le même contenu
from pipeline.pipeline import table, source_pg, source_mysql, ads, os

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")

# Nous allons comparer deux source de données
# Attention quand les deux sources viennent de base différentes (MySQL vs Postgre par exemple)
# Des types sont interprétés différemment et des grands DataFrames deviennent vite illisibles
# Ce sont les mêmes données mais il faut adpater les requêtes
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

dc = ads.DataComparator({
    'db_source_1': source_pg,
    'db_source_2': source_mysql,
    'query_source_1': query_pg,
    'query_source_2': query_mysql,
    'batch_size': 10_000 # par défaut à 10_000
}, logger)

# check_dtypes à True signifie qu'on va aussi faire attention aux types des données renvoyées
# la comparaison se fait par batchs, si une source termine avant l'autre ou si deux batchs sont différents, compare
# renvoie False
dc.compare(check_dtypes=True)