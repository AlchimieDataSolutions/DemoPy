# adstoolbox[pgsql]
"""
Écriture : les six méthodes d'insertion et de fusion.
"""
import os
import sys
from pathlib import Path

import adsToolBox as ads

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import utils  # noqa: E402

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
ads.set_timer(state=True)
env = ads.Env(logger=logger)

source = ads.DbPgsql(
    {
        "database": env.PG_DWH_DB,
        "user": env.PG_DWH_USER,
        "password": env.PG_DWH_PWD,
        "port": env.PG_DWH_PORT,
        "host": env.PG_DWH_HOST,
    },
    logger=logger,
)
source.connect()

table = "insert_test"
cols = [
    "id_int", "name_varchar", "code_char", "description_text", "count_int",
    "id_bigint", "amount_numeric", "price_numeric", "ratio_double",
    "score_real", "created_date", "created_at", "updated_at", "event_time",
    "is_active", "uuid_key",
]

# utils.build_data() remplace le jeu de données qui était recopié en dur
# dans ce script. Il est construit à la demande : 50 000 lignes, ~3,5 s.
data = utils.build_data(nb_lignes=50_000)

source.sql_exec(query=f"TRUNCATE TABLE {table};")

# ---------------------------------------------------------------------------
# 1. insert : UNE ligne
# ---------------------------------------------------------------------------
# `row` est une LISTE DE VALEURS, pas une liste de lignes. C'est la seule
# méthode du lot à prendre une ligne unique — d'où le nom du paramètre.
resultat = source.insert(
    schema="",           # "" ou None => table sans préfixe de schéma
    table=table,
    cols=cols,
    row=data[0],
)

# Les six méthodes renvoient le même triplet :
#   (statut, erreur, lignes en échec)
# avec statut à "SUCCESS" ou "ERROR". Elles ne LÈVENT pas d'exception sur un
# échec d'insertion : il faut tester le statut, sinon l'échec passe
# inaperçu. C'est ce mécanisme que Pipeline exploite pour consigner ses
# rejets sans interrompre le run.
statut, erreur, en_echec = resultat
logger.info(f"insert -> statut={statut}, erreur={erreur}")

# ---------------------------------------------------------------------------
# 2. insert_many : plusieurs lignes via executemany
# ---------------------------------------------------------------------------
# `rows` est une liste de listes. Passe par l'executemany du driver :
# une requête paramétrée, réexécutée pour chaque ligne.
statut, erreurs, rejets = source.insert_many(
    schema="", table=table, cols=cols, rows=data[1:1_001])
# On n'affiche PAS `rejets` : c'est la liste des lignes en échec, qui peut
# compter des milliers d'entrées et noyer la sortie. Elle est là pour être
# traitée, pas lue.
logger.info(f"insert_many -> {statut}, {len(rejets)} lot(s) rejeté(s)")

# ---------------------------------------------------------------------------
# 3. insert_bulk : plusieurs lignes en masse
# ---------------------------------------------------------------------------
# Nettement plus rapide sur du volume : la toolbox utilise le mécanisme de
# chargement en masse du backend (COPY sur PostgreSQL). À préférer dès
# quelques milliers de lignes.
#
# Contrepartie : le contrôle des erreurs est moins fin. Un lot en échec est
# rejeté en bloc, là où insert_many peut isoler la ligne fautive.
statut, erreurs, rejets = source.insert_bulk(
    schema="", table=table, cols=cols, rows=data[1_001:])
logger.info(f"insert_bulk -> {statut}, {len(rejets)} lot(s) rejeté(s)")

# ---------------------------------------------------------------------------
# 4. La contrainte d'unicité, prérequis de l'upsert
# ---------------------------------------------------------------------------
# Les trois méthodes d'upsert reposent sur ON CONFLICT : sans contrainte
# UNIQUE ou PRIMARY KEY sur les colonnes de conflit, la base refuse la
# requête. Elle n'est jamais créée automatiquement.
source.sql_exec(query=f"""
ALTER TABLE {table} DROP CONSTRAINT IF EXISTS unique_id_name;
ALTER TABLE {table} ADD CONSTRAINT unique_id_name UNIQUE (id_int, name_varchar);""")

# ---------------------------------------------------------------------------
# 5. upsert, upsert_many, upsert_bulk
# ---------------------------------------------------------------------------
# Même découpage que les trois insert, avec un paramètre de plus :
# conflict_cols, la LISTE des colonnes qui identifient une ligne existante.
# Elle doit correspondre exactement à la contrainte créée ci-dessus, et être
# un sous-ensemble de cols.
conflict_cols = cols[:2]   # ["id_int", "name_varchar"]

source.upsert(
    schema="",
    table=table,
    cols=cols,
    row=data[0],
    conflict_cols=conflict_cols,
)

source.upsert_many(
    schema="",
    table=table,
    cols=cols,
    rows=data[1:1_001],
    conflict_cols=conflict_cols,
)

# upsert_bulk crée une table temporaire, y charge les lignes en masse, puis
# fusionne en une seule requête. C'est le mode le plus rapide sur du volume.
source.upsert_bulk(
    schema="",
    table=table,
    cols=cols,
    rows=data[1_001:],
    conflict_cols=conflict_cols,
)

# PIÈGE : toutes les bases n'accordent pas le droit de créer des tables
# temporaires. Le cas s'est présenté en production sur une base PostgreSQL :
#
#   permission denied to create temporary tables in database "..."
#
# Depuis la 2026.10, upsert_bulk ne s'arrête plus là. Il bascule sur une
# table de travail ORDINAIRE, au nom unique, supprimée en fin de traitement,
# et vous prévient :
#
#   WARNING - Création d'une table temporaire refusée (...)
#   WARNING - Repli sur une table ORDINAIRE cible_staging_3f2326ec, supprimée
#             en fin de traitement. Accordez le droit de créer des tables
#             temporaires pour l'éviter.
#
# Le chargement en masse est conservé : repasser par upsert_many serait hors
# de portée sur du volume. Mesuré sur 20 000 lignes, les deux chemins donnent
# le même résultat.
#
# Le nom porte un suffixe aléatoire parce qu'une table ordinaire est visible
# de tous : elle ne doit écraser aucune table réelle ni gêner un autre
# traitement qui tournerait en même temps.
#
# SQL Server n'est pas concerné : sa table de travail est déjà persistante.
#
# Si la suppression finale n'a pas lieu — processus tué entre-temps — la
# table survit, contrairement à une temporaire qui disparaît avec la session.
# Son nom en `<table>_staging_<suffixe>` la rend reconnaissable.

# ---------------------------------------------------------------------------
# 6. Choisir
# ---------------------------------------------------------------------------
#   une ligne, ponctuellement            -> insert / upsert
#   quelques centaines, erreurs à isoler -> insert_many / upsert_many
#   milliers ou plus                     -> insert_bulk / upsert_bulk
#
# Pour un transfert entre deux bases, ne pilotez pas ces méthodes à la
# main : Pipeline s'en charge, avec les batchs, le typage et la collecte des
# rejets. Voir pipeline/pipeline.py, et pipeline_upsert.py pour l'upsert.

source.disconnect()