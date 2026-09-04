"""
ChangeDataCapture : capture de changement déclarative.

# adstoolbox[cdc]  (+ mssql pour cet exemple SQL Server)

Toutes les configurations possibles sont dans cdc_use.md, à côté de ce
fichier. Ce script en exécute une : mode scd2, historisation complète.
"""
import os

import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
ads.set_timer(state=True)
env = ads.Env(logger)

# ---------------------------------------------------------------------------
# 1. La chaîne de connexion
# ---------------------------------------------------------------------------
# ChangeDataCapture ne prend PAS une instance Db* mais une chaîne SQLAlchemy.
# C'est le seul objet de la toolbox dans ce cas : il s'appuie sur SQLAlchemy
# (extra cdc) pour générer le SQL des différents modes SCD.
#
# Le driver doit donc être installé en plus : mssql+pymssql exige l'extra
# mssql, postgresql+psycopg2 l'extra pgsql, mysql+pymysql l'extra mysql.
connection_string = f"mssql+pymssql://{env.AFT_USER}:{env.AFT_PWD}@{env.AFT_HOST}:{env.AFT_PORT}/{env.AFT_DB}"
config_json = """{
    "staging_area" : {
        "table" :         {"schema" : "nx_staging",  "name" : "AAA_test_pbx"},
        "pk_table" :      {"schema" : "nx_staging",  "name" : "AAA_test_pbx_pk"},
        "view" :          {"schema" : "nx_staging",  "name" : "v_AAA_test_pbx"},
        "cdc_table" :     {"schema" : "nx_cdc",      "name" : "AAA_test_pbx"}
    },
    "persistent_area" : {
        "table" :         {"schema" : "nx_business", "name" : "AAA_test_pbx"},
        "history_table" : {"schema" : "nx_business", "name" : "AAA_test_pbx_histo"},
        "view" :          {"schema" : "dbo",         "name" : "AAA_test_pbx"}
    },
    "mapping" : [
        {"position" :  1, "persistent_column" : "id",   "staging_column_or_expression" : "id",   "datatype" : "int",         "is_pk" : true,  "use_for_cdc" : false},
        {"position" :  2, "persistent_column" : "col1", "staging_column_or_expression" : "col1", "datatype" : "varchar(10)", "is_pk" : false, "use_for_cdc" : true },
        {"position" :  3, "persistent_column" : "col2", "staging_column_or_expression" : "col2", "is_pk" : false, "use_for_cdc" : true }
    ],
    "sync" : {
        "mode" : "scd2",
        "action_on_table" : {
            "truncate" : false,
            "delete_rows" : false,
            "delete_rows_condition" : null
        },
        "persistent_table_filter_expression" : null,
        "deleted_rows" : {
            "ignore" : false,
            "soft_delete" : false,
            "use_pk_table" : false
        },
        "technical_columns" : {
            "pk_hash" :           {"persistent_column" : "nx_pk_hash"},
            "row_hash" :          {"persistent_column" : "nx_row_hash"},
            "first_change_date" : {"persistent_column" : "nx_creation_date"},
            "last_change_date" :  {"persistent_column" : "nx_modification_date"},
            "is_active" :         {"persistent_column" : "nx_is_active"}
        },
        "distinct_rows" : false,
        "end_of_time_is_null" : true
    }
}"""

# ---------------------------------------------------------------------------
# 3. Exécution
# ---------------------------------------------------------------------------
# Trois arguments, tous positionnels dans la signature mais nommables :
#   config_json_string  la configuration, en CHAÎNE JSON (pas un dict)
#   connection_string   la chaîne SQLAlchemy ci-dessus
#   logger              un logger ads
#
# La configuration est validée par JSON Schema à l'instanciation : une clé
# manquante ou un mode inconnu échoue tout de suite, avec le chemin de
# l'erreur dans le message. C'est la seule classe de la toolbox à valider
# sa configuration ainsi.
cdc = ads.ChangeDataCapture(
    config_json_string=config_json,
    connection_string=connection_string,
    logger=logger,
)

# run() est la seule méthode publique. Elle enchaîne la préparation du
# staging, le calcul des différences et la synchronisation vers la table
# persistante, selon le mode déclaré dans sync.mode.
cdc.run()

# ---------------------------------------------------------------------------
# 4. Les quatre modes
# ---------------------------------------------------------------------------
# append   ajoute les nouvelles lignes, ne touche pas aux existantes
# scd1     écrase la ligne existante : pas d'historique
# scd2     clôt l'ancienne version et en insère une nouvelle : historique
#          complet, c'est le mode de cet exemple
# scd4     table courante + table d'historique séparée
#
# cdc_use.md donne une configuration complète pour chacun, ainsi que les
# variantes de gestion des suppressions (ignore, soft_delete, use_pk_table)
# et les colonnes techniques (pk_hash, row_hash, dates de changement,
# is_active).