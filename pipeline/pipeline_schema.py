# adstoolbox[mysql,pgsql]
"""
Pipeline : typage explicite plutôt qu'inféré.

Anciennement polars_inference.py. Renommé parce que le sujet n'est pas
l'inférence de Polars mais la clé cols_def du pipeline, et le gain à la
fournir.
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

table = "insert_test"
cols = [
    "id_int", "name_varchar", "code_char", "description_text", "count_int",
    "id_bigint", "amount_numeric", "price_numeric", "ratio_double",
    "score_real", "created_date", "created_at", "updated_at", "event_time",
    "is_active", "uuid_key",
]

# Les types SQL de la DESTINATION, dans le même ordre que cols. C'est la clé
# du script : sans elle, Polars devine ; avec elle, il applique.
cols_def = [
    "INTEGER", "VARCHAR(255)", "CHAR(100)", "TEXT", "INTEGER", "BIGINT",
    "NUMERIC(18,6)", "NUMERIC(10,2)", "DOUBLE PRECISION", "REAL", "DATE",
    "TIMESTAMP", "TIMESTAMP", "TIME", "INTEGER", "UUID",
]

source_mysql.connect()
source_mysql.sql_exec(query=f"DROP TABLE IF EXISTS {table};")
source_mysql.sql_exec(query=f"""
CREATE TABLE {table} (
    id_int INT, name_varchar VARCHAR(50), code_char CHAR(10), description_text TEXT,
    count_int INT, id_bigint BIGINT, amount_numeric DECIMAL(18,3),
    price_numeric DECIMAL(18,2), ratio_double DOUBLE, score_real REAL,
    created_date DATE, created_at DATETIME, updated_at DATETIME, event_time TIME,
    is_active BOOLEAN, uuid_key CHAR(36)
);""")
statut, _, rejets = source_mysql.insert_bulk(
    schema="", table=table, cols=cols, rows=utils.data)
logger.info(f"alimentation MySQL -> {statut}, {len(rejets)} lot(s) rejeté(s)")

query = f"""
SELECT id_int, name_varchar, code_char, description_text, count_int, id_bigint,
    amount_numeric, price_numeric, ratio_double, score_real, created_date,
    created_at, updated_at,
    TIME_FORMAT(event_time, '%H:%i:%s') AS event_time,
    is_active, uuid_key
FROM {table};
"""

destination = {
    "name": "demo",
    "db": dest_pg,
    "schema": "",
    "table": table,
    "cols": cols,
    "cols_def": cols_def,   # <- l'attribut important
}

pipe = ads.Pipeline(
    {
        "db_source": source_mysql,
        "query_source": query,
        "db_destination": destination,
    },
    logger=logger,
)

# ---------------------------------------------------------------------------
# 1. create_destination_table : créer la cible depuis cols + cols_def
# ---------------------------------------------------------------------------
# La méthode assemble le CREATE TABLE à partir des deux listes. Elle n'est
# donc utilisable QUE si cols_def est fourni.
#
# drop=True supprime la table avant de la recréer : destructeur, à réserver
# aux rechargements complets. drop=False (défaut) laisse une table existante
# en place — le message "La table de destination existe déjà" est alors un
# warning, pas une erreur.
pipe.create_destination_table(drop=True)

# Contrôle de cohérence intégré : si len(cols) != len(cols_def), un
# ValueError explicite est levé, avec les deux longueurs. C'est le seul
# endroit du pipeline où cet écart est détecté tôt.

# ---------------------------------------------------------------------------
# 2. Traduire les types SQL en types Polars
# ---------------------------------------------------------------------------
# sql_defs_to_polars_schema fait la conversion utilisée en interne par
# run(). L'appeler directement sert à VÉRIFIER la correspondance avant de
# lancer un transfert de plusieurs millions de lignes.
schema = pipe.sql_defs_to_polars_schema(cols=cols, cols_def=cols_def)
for nom, dtype in schema.items():
    logger.info(message=f"  {nom:20s} -> {dtype}")

# Quatre comportements à connaître.
#
# a) cols_def ne garantit pas le type qu'on imagine. Regardez la sortie
#    ci-dessus : amount_numeric et price_numeric donnent String, pas un
#    type numérique.
#
#    C'est VOULU. Un Float64 perd la précision au-delà d'une quinzaine de
#    chiffres significatifs : un aller-retour sur NUMERIC(18,6) transforme
#    123456789012.345678 en 123456789012.345670. Le texte préserve la
#    valeur, et PostgreSQL la reconvertit à l'insertion. DECIMAL, MONEY et
#    SMALLMONEY suivent la même règle.
#
#    Jusqu'à la 2026.10.13, DOUBLE PRECISION, REAL et UUID retombaient eux
#    aussi en Utf8, faute d'être dans la table de correspondance — avec un
#    simple log DEBUG "Type SQL non reconnu". Ils sont désormais résolus,
#    respectivement en Float64, Float64 et String.
#
# a bis) Une FAUTE DE FRAPPE produit exactement le même repli, donc le même
#    silence. "NUMERICC" ci-dessous donne une colonne texte sans que rien
#    ne signale l'erreur ailleurs que dans les logs DEBUG.
schema_faute = pipe.sql_defs_to_polars_schema(
    cols=["montant"],
    cols_def=["NUMERICC(18,2)"],   # faute volontaire
)
logger.warning(message=f"Type mal orthographié -> {schema_faute}")

# b) Seule la partie avant la parenthèse est lue : VARCHAR(255) et
#    VARCHAR(10) donnent le même pl.Utf8. Les longueurs ne servent qu'au
#    CREATE TABLE, pas au typage Polars.
logger.info(message=str(pipe.sql_defs_to_polars_schema(
    cols=["a", "b"], cols_def=["VARCHAR(255)", "VARCHAR(10)"],
)))

# c) Si cols et cols_def n'ont PAS la même longueur, l'erreur est
#    déroutante : "ValueError: zip() argument 2 is shorter than argument 1",
#    sans mention de cols ni de cols_def. Pire, dans run() cette exception
#    est attrapée par la gestion de batch et devient "Échec de la création
#    du dataframe" sur CHAQUE batch, donc toutes les lignes rejetées.
#    create_destination_table(), lui, contrôle les longueurs et lève un
#    message clair : appelez-le d'abord, même avec drop=False, pour valider
#    la cohérence avant le transfert.
#
# d) Cas particulier MySQL : une colonne TIME issue d'une source MySQL est
#    forcée en Utf8, quel que soit cols_def, parce que le format renvoyé par
#    le driver n'est pas convertible en pl.Time. C'est le pendant du
#    TIME_FORMAT de la requête.

# ---------------------------------------------------------------------------
# 3. Exécution
# ---------------------------------------------------------------------------
# Avec cols_def, Polars n'infère plus : il applique le schéma dès le premier
# batch. Comparez les logs de ce script avec ceux de pipeline.py — la ligne
# "DEBUG - Inférence des types sur le premier batch." n'apparaît qu'ici.
#
# Le gain n'est PAS celui qu'on imagine. L'inférence n'a lieu qu'une fois,
# sur le premier lot, pas à chaque lot : son coût est donc borné et négligeable
# face aux entrées-sorties. Mesuré sur ce jeu de 50 000 lignes, en alternant
# l'ordre des essais pour écarter l'effet d'échauffement :
#
#   avec cols_def   1.19s   1.22s
#   sans cols_def   1.31s   1.22s
#
# Aucun écart significatif. Le vrai intérêt de cols_def est ailleurs :
#
#   - typage DÉTERMINISTE : l'inférence dépend du contenu du premier lot,
#     donc du tri, du filtre, de la volumétrie. Deux exécutions sur des
#     données différentes peuvent produire deux schémas différents.
#   - protection contre les colonnes entièrement nulles, qui restent pl.Null
#     et font échouer l'insertion (voir la fin de ce script).
#   - conversion explicite plutôt que devinée, donc des surprises qui
#     apparaissent à la lecture du code et non en production.
resultats = pipe.run()
# On ne journalise PAS le dictionnaire entier : sa clé 'errors' contient les
# lignes rejetées, donc potentiellement des milliers d'entrées.
logger.info(f"{resultats['nb_lines_success']} ligne(s) insérée(s), "
            f"{resultats['nb_lines_error']} en erreur")
for nom, cause, lignes in resultats["errors"]:
    logger.warning(f"  {nom} : {cause} sur {len(lignes)} ligne(s)")

# La table des types s'étoffe au fil des versions : elle est passée de 15 à
# 31 entrées en 2026.10.13, couvrant désormais les types courants de
# PostgreSQL, MySQL et SQL Server. Relancez ce script après chaque montée de
# version : toute ligne "Type SQL non reconnu" restante désigne soit une
# faute de frappe, soit un type encore absent.

# Sans cols_def, le comportement est celui de pipeline.py : inférence sur le
# premier batch, réinférence partielle des colonnes restées pl.Null sur les
# batchs suivants. Une colonne entièrement nulle sur TOUT le run reste
# pl.Null, un type qui ne correspond à aucune colonne SQL et fera échouer
# l'insertion. Fournir cols_def est la seule protection contre ce cas.

source_mysql.disconnect()
dest_pg.disconnect()