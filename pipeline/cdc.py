# adstoolbox[cdc,pgsql]
"""
ChangeDataCapture : capture de changement déclarative.

Ce script est EXÉCUTABLE tel quel sur la base PostgreSQL de la démo. Il
fabrique sa propre table source depuis insert_test, lance deux
synchronisations successives et montre l'historisation du mode scd2.

Toutes les configurations possibles sont dans cdc_use.md, à côté de ce
fichier.

PRÉREQUIS : lancez `python pipeline/pipeline.py` avant, pour disposer de la
table insert_test dont ce script tire ses données.
"""
import json
import os

import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.INFO, f"adsLogger - {script_name}")
ads.set_timer(state=True)
env = ads.Env(logger)

SCHEMA = "public"
SOURCE = "cdc_source"        # table de staging, rechargée à chaque passage
VUE = "v_cdc_source"         # vue de staging, construite par le CDC
DIFF = "cdc_diff"            # table CDC : le différentiel du passage courant
CIBLE = "cdc_cible"          # table persistante, historisée

# ---------------------------------------------------------------------------
# 1. La chaîne de connexion
# ---------------------------------------------------------------------------
# ChangeDataCapture ne prend PAS une instance Db* mais une chaîne SQLAlchemy.
# C'est le seul objet de la toolbox dans ce cas : il s'appuie sur SQLAlchemy
# (extra cdc) pour générer le SQL des différents modes SCD.
#
# Le driver doit donc être installé en plus : postgresql+psycopg2 exige
# l'extra pgsql, mssql+pymssql l'extra mssql, mysql+pymysql l'extra mysql.
# Depuis la 2026.10, un driver manquant est signalé clairement plutôt que par
# un ModuleNotFoundError nu, le chargement paresseux ne voyant pas ce cas
# puisque c'est SQLAlchemy qui importe le driver :
#
#   ImportError: La chaîne de connexion utilise le pilote 'mssql+pymssql',
#   dont le driver Python 'pymssql' n'est pas installé. Installez-le avec :
#   pip install "adstoolbox[mssql]" (l'extra "cdc" n'apporte que SQLAlchemy).
connection_string = (
    f"postgresql+psycopg2://{env.PG_DWH_USER}:{env.PG_DWH_PWD}"
    f"@{env.PG_DWH_HOST}:{env.PG_DWH_PORT}/{env.PG_DWH_DB}"
)

# ---------------------------------------------------------------------------
# 2. Prérequis côté base : l'extension pgcrypto
# ---------------------------------------------------------------------------
# Sur PostgreSQL uniquement, l'empreinte de clé passe par digest(), fourni
# par pgcrypto et absent d'une installation nue. ChangeDataCapture le vérifie
# au démarrage et indique quoi faire, plutôt que d'échouer au milieu du calcul.
#
# L'empreinte de ligne, elle, utilise md5() qui est natif : seul SHA2-256
# impose l'extension. SQL Server n'est pas concerné, il passe par HASHBYTES.
#
# L'activation demande des droits d'administration : sur une base managée,
# elle doit être faite par l'administrateur, à anticiper avant la production.
db = ads.DbPgsql(
    {
        "database": env.PG_DWH_DB,
        "user": env.PG_DWH_USER,
        "password": env.PG_DWH_PWD,
        "port": env.PG_DWH_PORT,
        "host": env.PG_DWH_HOST,
    },
    logger=logger,
)
db.connect()
db.sql_exec(query="CREATE EXTENSION IF NOT EXISTS pgcrypto;")


# ---------------------------------------------------------------------------
# 3. Alimentation du staging
# ---------------------------------------------------------------------------
# Le staging doit être RECHARGÉ à chaque synchronisation. Les colonnes
# d'empreinte, ajoutées par le CDC, doivent repartir vides : sinon le CDC
# considère les empreintes déjà calculées et compare des valeurs périmées.
#
# Un DROP/CREATE est le plus simple ici ; en production le rechargement vient
# de l'alimentation en amont (Pipeline, COPY, etc.).
def charger_staging(decalage: int) -> None:
    """Recharge la table de staging depuis insert_test, avec un décalage."""
    db.sql_exec(query=f"DROP TABLE IF EXISTS {SCHEMA}.{SOURCE} CASCADE;")
    db.sql_exec(query=f"""
    CREATE TABLE {SCHEMA}.{SOURCE} AS
    SELECT id_int AS id,
           name_varchar AS nom,
           count_int + {decalage} AS compteur
    FROM insert_test
    WHERE id_int <= 100;""")


charger_staging(decalage=0)

# On repart d'une cible vide pour que le script soit rejouable.
db.sql_exec(query=f"DROP TABLE IF EXISTS {SCHEMA}.{CIBLE} CASCADE;")
db.sql_exec(query=f"DROP TABLE IF EXISTS {SCHEMA}.{DIFF} CASCADE;")
db.sql_exec(query=f"DROP VIEW IF EXISTS {SCHEMA}.{VUE} CASCADE;")

# ---------------------------------------------------------------------------
# 4. La configuration
# ---------------------------------------------------------------------------
# Elle est validée par JSON Schema à l'instanciation : une clé manquante ou
# un mode inconnu échoue tout de suite, avec le chemin de l'erreur dans le
# message. C'est la seule classe de la toolbox à valider sa configuration
# ainsi.
#
# is_pk désigne les colonnes qui identifient une ligne, use_for_cdc celles
# dont un changement doit être détecté. Une colonne peut n'être ni l'une ni
# l'autre : elle est alors recopiée sans participer à la comparaison.
config = {
    "staging_area": {
        "table": {"schema": SCHEMA, "name": SOURCE},
        "view": {"schema": SCHEMA, "name": VUE},
        "cdc_table": {"schema": SCHEMA, "name": DIFF},
    },
    "persistent_area": {
        "table": {"schema": SCHEMA, "name": CIBLE},
    },
    "mapping": [
        {"position": 1, "persistent_column": "id", "staging_column_or_expression": "id",
         "datatype": "INTEGER", "is_pk": True, "use_for_cdc": False},
        {"position": 2, "persistent_column": "nom", "staging_column_or_expression": "nom",
         "datatype": "VARCHAR(255)", "is_pk": False, "use_for_cdc": True},
        {"position": 3, "persistent_column": "compteur",
         "staging_column_or_expression": "compteur",
         "datatype": "INTEGER", "is_pk": False, "use_for_cdc": True},
    ],
    "sync": {
        "mode": "scd2",
        "deleted_rows": {"ignore": False, "soft_delete": False, "use_pk_table": False},
        "technical_columns": {
            "pk_hash": {"persistent_column": "nx_pk_hash"},
            "row_hash": {"persistent_column": "nx_row_hash"},
            "first_change_date": {"persistent_column": "nx_creation_date"},
            "last_change_date": {"persistent_column": "nx_modification_date"},
            "is_active": {"persistent_column": "nx_is_active"},
        },
        "distinct_rows": False,
        "end_of_time_is_null": True,
    },
}

# ---------------------------------------------------------------------------
# 5. Première synchronisation : tout est nouveau
# ---------------------------------------------------------------------------
# Trois arguments, tous positionnels dans la signature mais nommables :
#   config_json_string  la configuration, en CHAÎNE JSON (pas un dict)
#   connection_string   la chaîne SQLAlchemy ci-dessus
#   logger              un logger ads
#
# run() est la seule méthode publique. Elle enchaîne la préparation du
# staging, le calcul des empreintes, la détection des différences et la
# synchronisation vers la table persistante, selon sync.mode.
ads.ChangeDataCapture(
    config_json_string=json.dumps(config),
    connection_string=connection_string,
    logger=logger,
).run()

total = db.sql_scalaire(query=f"SELECT COUNT(*) FROM {CIBLE}")
logger.info(f"après le 1er passage : {total} ligne(s)")

# ---------------------------------------------------------------------------
# 6. Deuxième synchronisation : les lignes modifiées sont historisées
# ---------------------------------------------------------------------------
# On recharge le staging avec un compteur décalé : les 100 lignes ont donc
# toutes changé. En scd2, la version précédente est CLOSE et une nouvelle est
# insérée — la table contient alors l'historique complet.
charger_staging(decalage=1_000)

ads.ChangeDataCapture(
    config_json_string=json.dumps(config),
    connection_string=connection_string,
    logger=logger,
).run()

total = db.sql_scalaire(query=f"SELECT COUNT(*) FROM {CIBLE}")
actives = db.sql_scalaire(query=f"SELECT COUNT(*) FROM {CIBLE} WHERE nx_is_active")
logger.info(f"après le 2e passage : {total} ligne(s) dont {actives} active(s)")

# Une seule version active par clé, deux versions au total pour chacune.
# Avec end_of_time_is_null, la version courante porte une date de fin NULL
# plutôt qu'une sentinelle au 31/12/9999 : à choisir selon que vos requêtes
# filtrent sur `IS NULL` ou sur une comparaison de dates.
for ligne in next(iter(db.sql_query(query=f"""
        SELECT compteur, nx_is_active, nx_modification_date
        FROM {CIBLE} WHERE id = 1 ORDER BY nx_is_active""")), []):
    logger.info(f"  id=1 -> compteur={ligne[0]}, active={ligne[1]}, fin={ligne[2]}")

# Le différentiel du passage courant est dans la table CDC. Elle est vidée et
# recréée à chaque exécution : la conserver mélangerait deux lots.
for ligne in next(iter(db.sql_query(query=f"""
        SELECT operation, COUNT(*) FROM {DIFF} GROUP BY operation""")), []):
    logger.info(f"  différentiel : opération {ligne[0]} sur {ligne[1]} ligne(s)")

# ---------------------------------------------------------------------------
# 7. Les quatre modes
# ---------------------------------------------------------------------------
# append   ajoute les nouvelles lignes, ne touche pas aux existantes
# scd1     écrase la ligne existante : pas d'historique
# scd2     clôt l'ancienne version et en insère une nouvelle : historique
#          complet, c'est le mode de cet exemple
# scd4     table courante + table d'historique séparée, déclarée par
#          persistent_area.history_table
#
# cdc_use.md donne une configuration complète pour chacun, ainsi que les
# variantes de gestion des suppressions (ignore, soft_delete, use_pk_table)
# et les colonnes techniques.

db.disconnect()