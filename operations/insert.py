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
print(source.insert_many(schema="", table=table, cols=cols, rows=data[1:1_000]))

# ---------------------------------------------------------------------------
# 3. insert_bulk : plusieurs lignes en masse
# ---------------------------------------------------------------------------
# Nettement plus rapide sur du volume : la toolbox utilise le mécanisme de
# chargement en masse du backend (COPY sur PostgreSQL). À préférer dès
# quelques milliers de lignes.
#
# Contrepartie : le contrôle des erreurs est moins fin. Un lot en échec est
# rejeté en bloc, là où insert_many peut isoler la ligne fautive.
print(source.insert_bulk(schema="", table=table, cols=cols, rows=data[1_001:]))

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
    rows=data[1:1_000],
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