# adstoolbox[pgsql]
"""
Pipeline : sources non-SQL (tableau en mémoire, API REST).

Regroupe les anciens pipeline_tableau.py et pipeline_api.py : les deux
illustraient la même chose, une source fournie par la clé 'tableau' plutôt
que par 'db_source'. Seule l'origine des lignes change.
"""
import os
import sys
from pathlib import Path

import adsToolBox as ads

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import utils  # noqa: E402
from get_api_data import NxOnyxApi  # noqa: E402

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
ads.set_timer(state=True)
env = ads.Env(logger=logger)

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


def resumer(resultats: dict, libelle: str) -> None:
    """
    Journalise un résultat de run() sans déverser les lignes rejetées.

    PIÈGE : la clé 'errors' contient les DONNÉES en échec, pas seulement la
    cause. Journaliser le dictionnaire entier peut produire des milliers de
    lignes — le DataFrame complet et chaque tuple rejeté. Elle est là pour
    être rejouée, pas lue.
    """
    logger.info(
        f"{libelle} : {resultats['nb_lines_success']} ligne(s) insérée(s), "
        f"{resultats['nb_lines_error']} en erreur",
    )
    for nom, cause, lignes in resultats["errors"]:
        logger.warning(f"  {nom} : {cause} sur {len(lignes)} ligne(s)")


# ---------------------------------------------------------------------------
# 1. Source = tableau en mémoire
# ---------------------------------------------------------------------------
# Avec 'tableau', il n'y a NI db_source NI query_source. Le pipeline découpe
# lui-même la liste en batchs de batch_size lignes.
#
# Le tableau est une liste de séquences (listes ou tuples), chaque séquence
# dans l'ordre des colonnes de db_destination['cols'].
cols = [
    "id_int", "name_varchar", "code_char", "description_text", "count_int",
    "id_bigint", "amount_numeric", "price_numeric", "ratio_double",
    "score_real", "created_date", "created_at", "updated_at", "event_time",
    "is_active", "uuid_key",
]

destination = {
    "name": "demo",
    "db": dest_pg,
    "schema": "",
    "table": "insert_test",
    "cols": cols,
}

pipe = ads.Pipeline(
    {
        # Pas de 'db_source', pas de 'query_source'.
        "tableau": utils.build_data(nb_lignes=1_000),
        "db_destination": destination,
        # operation_type 'insert' et insert_method 'bulk' par défaut.
        "batch_size": 500,
    },
    logger=logger,
)

resumer(pipe.run(), "tableau")

# Différence de comportement à connaître : avec 'tableau', le pipeline ne
# connaît pas les types SQL de la source. Sans cols_def, Polars infère donc
# depuis les valeurs Python — ce qui marche bien avec des date/datetime/UUID
# natifs, moins bien avec des chaînes ambiguës. Voir pipeline_schema.py.

# ---------------------------------------------------------------------------
# 2. Source = API REST
# ---------------------------------------------------------------------------
# Même mécanisme : on récupère les données, on les met en forme, on les passe
# par 'tableau'. get_api_data.py fournit le client d'exemple.
#
# L'appel réel n'a lieu que si les variables d'API sont renseignées. On passe
# par env.get() et non par env.API_DOMAIN : l'accès par ATTRIBUT lève une
# AttributeError sur une variable absente, alors que get() renvoie None.
# C'est exactement la différence montrée dans logger/env.py, et elle permet
# ici de rendre la section optionnelle.
if env.get("API_DOMAIN"):
    api = NxOnyxApi(
        domain=env.API_DOMAIN,
        username=env.API_USER,
        password=env.API_PASSWORD,
        tenantId=env.TENANT_ID,
    )
    donnees = api.getTree()
else:
    # Charge utile simulée, de la même forme que celle de l'API : une liste
    # de dictionnaires. La suite de la section reste donc démontrable sans
    # accès réseau.
    logger.warning("Variables d'API absentes : on poursuit sur une charge simulée.")
    donnees = [
        {"id": 1, "categoryId": 10, "name": "Racine", "isExpanded": True},
        {"id": 2, "categoryId": 10, "name": "Enfant A", "isExpanded": False},
        {"id": 3, "categoryId": 20, "name": "Enfant B", "isExpanded": False},
    ]

# L'API renvoie des DICTIONNAIRES, comme OdooConnector.get(). Le pipeline
# attend des séquences de valeurs : il faut convertir. Le point délicat est
# l'ORDRE — dict.values() suit l'ordre d'insertion des clés, qui doit donc
# correspondre à celui de db_destination['cols'].
noms_cles = list(donnees[0].keys())
valeurs_tuples = [tuple(d.values()) for d in donnees]

logger.info(message=f"Clés de l'API : {noms_cles}")
logger.info(message=f"{len(valeurs_tuples)} ligne(s) récupérée(s)")

# Plus robuste que dict.values() : imposer l'ordre explicitement. Une clé
# absente d'un enregistrement donne None au lieu de décaler toute la ligne.
colonnes_api = ["id", "categoryId", "name", "isExpanded"]
valeurs_tuples = [tuple(d.get(c) for c in colonnes_api) for d in donnees]

destination_api = {
    "name": "api",
    "db": dest_pg,
    "schema": "",
    "table": "demo_pipeline",
    "cols": colonnes_api,
}

# ---------------------------------------------------------------------------
# 3. Le piège des clés au premier niveau
# ---------------------------------------------------------------------------
# L'ancien pipeline_api.py écrivait ceci :
#
#   ads.Pipeline({
#       "tableau": valeurs_tuples,
#       "db_destination": destination,
#       "table": "onyx_qs.test",     # <- IGNORÉ
#       "cols": noms_cles,           # <- IGNORÉ
#   }, logger)
#
# 'table' et 'cols' ne sont PAS lus au premier niveau : ils appartiennent à
# db_destination. Aucune erreur, aucun avertissement — les valeurs étaient
# simplement sans effet, et le pipeline utilisait celles de destination.
#
# C'est la conséquence directe du .get() sur un dictionnaire libre : toute
# faute de placement ou de frappe passe inaperçue. Relisez vos clés.
# La table cible doit exister : on la crée depuis cols_def, ce qui permet
# aussi de typer explicitement une source qui n'a pas de types SQL.
pipeline_api = ads.Pipeline(
    {
        "tableau": valeurs_tuples,
        "db_destination": {**destination_api,
                           "cols_def": ["INTEGER", "INTEGER", "VARCHAR(255)", "BOOLEAN"]},
    },
    logger=logger,
)
pipeline_api.create_destination_table(drop=True)

resumer(pipeline_api.run(), "API")

dest_pg.disconnect()