# adstoolbox[mysql,pgsql]
"""
Pipeline : la référence, source SQL vers destination SQL.

Script de référence du dossier. Les autres démontrent une variation :
  pipeline_sources.py   source non-SQL : tableau en mémoire, API
  pipeline_upsert.py    operation_type='upsert' et conflict_cols
  pipeline_hash.py      déduplication par empreinte
  pipeline_schema.py    typage explicite plutôt qu'inféré
  cdc.py                ChangeDataCapture
"""
import os
import sys
from pathlib import Path

import adsToolBox as ads

# utils.py vit à la racine du dépôt : il faut l'ajouter au chemin pour que
# ce script reste lançable par `python pipeline/pipeline.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import utils  # noqa: E402

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
ads.set_timer(state=True)
env = ads.Env(logger=logger)

# ---------------------------------------------------------------------------
# 1. Source et destination
# ---------------------------------------------------------------------------
# MySQL en source, PostgreSQL en destination : le pipeline traverse deux
# technologies, c'est son intérêt principal.
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
source_mysql.connect()

dest_pg = ads.DbPgsql(
    {
        "database": env.PG_DWH_DB,
        "user": env.PG_DWH_USER,
        "password": env.PG_DWH_PWD,
        "port": env.PG_DWH_PORT,
        "host": env.PG_DWH_HOST,
    },
    logger=logger,
)
dest_pg.connect()

table = "insert_test"

# Colonnes de la table de démonstration, dans l'ordre des valeurs de
# utils.data. utils.COLS_DEF donne les types SQL correspondants.
cols = [
    "id_int", "name_varchar", "code_char", "description_text", "count_int",
    "id_bigint", "amount_numeric", "price_numeric", "ratio_double",
    "score_real", "created_date", "created_at", "updated_at", "event_time",
    "is_active", "uuid_key",
]

# ---------------------------------------------------------------------------
# 2. Préparer les deux tables
# ---------------------------------------------------------------------------
source_mysql.sql_exec(query=f"DROP TABLE IF EXISTS {table};")
source_mysql.sql_exec(query=f"""
CREATE TABLE {table} (
    id_int INT, name_varchar VARCHAR(50), code_char CHAR(10), description_text TEXT,
    count_int INT, id_bigint BIGINT, amount_numeric DECIMAL(18,3),
    price_numeric DECIMAL(18,2), ratio_double DOUBLE, score_real REAL,
    created_date DATE, created_at DATETIME, updated_at DATETIME, event_time TIME,
    is_active BOOLEAN, uuid_key CHAR(36)
);""")

# utils.data est désormais construit à la demande : 50 000 lignes, ~3,5 s au
# premier accès. utils.build_data(nb_lignes=100) pour aller plus vite.
print(source_mysql.insert_bulk(schema="", table=table, cols=cols, rows=utils.data))
dest_pg.sql_exec(query=f"DROP TABLE IF EXISTS {table};")
dest_pg.sql_exec(query=f"""
CREATE TABLE {table} (
    id_int INTEGER, name_varchar VARCHAR(255), code_char CHAR(100),
    description_text TEXT, count_int INTEGER, id_bigint BIGINT,
    amount_numeric NUMERIC(18,6), price_numeric NUMERIC(10,2),
    ratio_double DOUBLE PRECISION, score_real REAL, created_date DATE,
    created_at TIMESTAMP, updated_at TIMESTAMP, event_time TIME,
    is_active INTEGER, uuid_key UUID
);""")

# ---------------------------------------------------------------------------
# 3. La requête source, et les deux pièges de portabilité
# ---------------------------------------------------------------------------
# MySQL renvoie les colonnes TIME sous une forme que Polars n'infère pas :
# il faut les formater côté SQL avec TIME_FORMAT.
#
# SQL Server en source exige CAST(uuid_col AS NVARCHAR(36)) pour les
# UNIQUEIDENTIFIER, sinon la valeur est illisible.
#
# Pipeline connaît ces deux cas : quand la construction du DataFrame échoue,
# il ajoute le rappel correspondant au message d'erreur selon le type de la
# source. Lisez donc les logs en entier avant de chercher ailleurs.
query = f"""
SELECT id_int, name_varchar, code_char, description_text, count_int, id_bigint,
    amount_numeric, price_numeric, ratio_double, score_real, created_date,
    created_at, updated_at,
    TIME_FORMAT(event_time, '%H:%i:%s') AS event_time,
    is_active, uuid_key
FROM {table};
"""

# ---------------------------------------------------------------------------
# 4. Le dictionnaire de destination
# ---------------------------------------------------------------------------
# Huit clés possibles, toutes lues via .get() :
#   db             OBLIGATOIRE, l'instance Db* cible
#   table          nom de la table cible
#   schema         schéma ; "" ou absent => table sans préfixe
#   cols           colonnes cibles, dans l'ordre des valeurs de la source
#   cols_def       types SQL ; voir pipeline_schema.py
#   hash           colonne d'empreinte ; voir pipeline_hash.py
#   conflict_cols  clés de conflit pour l'upsert ; voir pipeline_upsert.py
#   name           libellé pour les logs, "bdd" par défaut
destination = {
    "name": "demo",
    "db": dest_pg,
    "schema": "",
    "table": table,
    "cols": cols,
}

# ---------------------------------------------------------------------------
# 5. Le dictionnaire du pipeline
# ---------------------------------------------------------------------------
# ATTENTION : seules ces sept clés sont lues au premier niveau. Toute autre
# clé est IGNORÉE SILENCIEUSEMENT. Placer 'table' ou 'cols' ici au lieu de
# db_destination ne produit aucune erreur, simplement aucun effet.
pipe = ads.Pipeline(
    {
        "db_source": source_mysql,      # exclusif avec 'tableau'
        "query_source": query,          # requis avec db_source
        "tableau": None,                # exclusif avec db_source
        "db_destination": destination,
        "operation_type": "insert",     # 'insert' (défaut) ou 'upsert'
        "insert_method": "bulk",        # 'bulk' (défaut) ou 'executemany'
        "batch_size": 10_000,           # défaut 10 000
    },
    logger=logger,
)

# batch_size du pipeline ÉCRASE celui des objets db_source et db_destination :
# inutile de le régler sur les connexions, c'est le pipeline qui décide.

# Fournir à la fois 'tableau' et 'db_source' lève un ValueError explicite
# ("On veut tous le beurre et l'argent du beurre..."). N'en fournir aucun
# lève "Aucune source de données choisie."

# ---------------------------------------------------------------------------
# 6. Exécution et lecture des résultats
# ---------------------------------------------------------------------------
resultats = pipe.run()
print(f"Résultats : {resultats}")

# run() renvoie toujours un dictionnaire à trois clés :
#   nb_lines_success  lignes insérées
#   nb_lines_error    lignes rejetées
#   errors            liste de tuples (nom, cause, données rejetées)
#
# POINT IMPORTANT : run() ne lève PAS d'exception sur un batch en erreur. Il
# poursuit avec les batchs suivants et consigne les rejets. Un run sans
# exception peut donc avoir tout rejeté : testez nb_lines_error, jamais
# l'absence d'exception.
if resultats["nb_lines_error"]:
    logger.warning(message=f"{resultats['nb_lines_error']} ligne(s) rejetée(s)")
    for nom, cause, lignes in resultats["errors"]:
        logger.warning(message=f"  {nom} : {cause} sur {len(lignes)} ligne(s)")

# Les données rejetées sont conservées dans errors : elles peuvent être
# rejouées après correction, sans relire la source.
#
# En revanche une erreur AUTRE qu'un échec d'insertion (connexion perdue,
# operation_type inconnu) est propagée après journalisation.

# ---------------------------------------------------------------------------
# 7. Typage : par inférence ici
# ---------------------------------------------------------------------------
# Sans cols_def, Polars infère les types sur le premier batch et conserve ce
# schéma pour tout le run. Si une colonne n'a pas pu être typée (entièrement
# nulle sur le premier batch), une réinférence PARTIELLE est faite sur les
# batchs suivants jusqu'à obtenir un schéma complet.
#
# Fournir cols_def évite cette inférence : voir pipeline_schema.py.

source_mysql.disconnect()
dest_pg.disconnect()