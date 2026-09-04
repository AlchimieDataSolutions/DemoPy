"""
DataFactory : l'interface commune aux trois bases.

# adstoolbox[mssql,mysql,pgsql]

DataFactory est la classe abstraite dont héritent DbMssql, DbMysql et
DbPgsql. On ne l'instancie jamais directement : elle sert à écrire du code
qui fonctionne avec n'importe quel backend.
"""
import os

import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
env = ads.Env(logger)

# ---------------------------------------------------------------------------
# 1. DataFactory ne s'instancie pas
# ---------------------------------------------------------------------------
# C'est une classe abstraite : elle définit le contrat, pas l'implémentation.
try:
    ads.DataFactory(dictionnary={}, logger=logger)
except TypeError as e:
    logger.info(f"DataFactory est abstraite, comme prévu : {e}")

# ---------------------------------------------------------------------------
# 2. Le contrat commun
# ---------------------------------------------------------------------------
# Toute sous-classe expose les mêmes méthodes. Les lister depuis la classe
# abstraite évite de deviner ce qui est portable d'un backend à l'autre.
contrat = sorted(
    m for m in dir(ads.DataFactory)
    if not m.startswith("_") and callable(getattr(ads.DataFactory, m, None))
)
logger.info(f"Méthodes du contrat DataFactory : {', '.join(contrat)}")

# ---------------------------------------------------------------------------
# 3. Écrire une fonction qui accepte n'importe quel backend
# ---------------------------------------------------------------------------
# Typez sur DataFactory, jamais sur DbPgsql : la fonction devient réutilisable
# sans modification quand la source change de technologie.


def compter_lignes(db: ads.DataFactory, table: str, logger: ads.Logger) -> int:
    """Compte les lignes d'une table, quel que soit le backend."""
    db.connect()
    resultat = db.sql_scalaire(query=f"SELECT COUNT(*) FROM {table}")  # noqa: S608
    logger.info(f"{type(db).__name__} : {resultat} ligne(s) dans {table}")
    return resultat

# Les trois connexions, construites de la même façon à un détail près.
bases = {
    "pgsql": ads.DbPgsql(
        {
            "database": env.PG_DWH_DB,
            "user": env.PG_DWH_USER,
            "password": env.PG_DWH_PWD,
            "port": env.PG_DWH_PORT,
            "host": env.PG_DWH_HOST,
        },
        logger=logger,
        batch_size=10,
    ),
    "mysql": ads.DbMysql(
        {
            "database": env.MYSQL_DWH_DB,
            "user": env.MYSQL_DWH_USER,
            "password": env.MYSQL_DWH_PWD,
            "port": env.MYSQL_DWH_PORT,
            "host": env.MYSQL_DWH_HOST,
        },
        logger=logger,
        batch_size=10,
    ),
    # MSSQL accepte en plus `charset`, UTF-8 par défaut.
    "mssql": ads.DbMssql(
        {
            "database": env.MSSQL_DWH_DB,
            "user": env.MSSQL_DWH_USER,
            "password": env.MSSQL_DWH_PWD,
            "port": env.MSSQL_DWH_PORT,
            "host": env.MSSQL_DWH_HOST,
            "charset": "UTF-8",
        },
        logger=logger,
        batch_size=10,
    ),
}

# ---------------------------------------------------------------------------
# 4. Ce qui reste spécifique malgré l'interface commune
# ---------------------------------------------------------------------------
# L'interface est portable, le SQL ne l'est pas. Les écarts à connaître :
#
#   - types : TIMESTAMP (Postgres/MySQL) vs DATETIME2 (SQL Server) ;
#             UUID (Postgres) vs UNIQUEIDENTIFIER vs CHAR(36) (MySQL)
#   - MySQL renvoie les colonnes TIME dans un format que Polars n'infère pas :
#     passez par TIME_FORMAT(col, '%H:%i:%s') — Pipeline le signale déjà
#   - SQL Server exige CAST(uuid_col AS NVARCHAR(36)) pour les UUID
#   - `CREATE TABLE IF NOT EXISTS` n'existe pas sur SQL Server, qui demande
#     IF OBJECT_ID(...) IS NULL
#
# Voir operations/compare.py pour un exemple d'adaptation des requêtes entre
# Postgres et MySQL sur des données identiques.

for nom, db in bases.items():
    try:
        compter_lignes(db, "LOGS", logger)
    except Exception as e:  # noqa: BLE001
        # Chaque base peut être absente de l'environnement de démo.
        logger.warning(f"{nom} indisponible : {e}")
    finally:
        db.disconnect()

logger.info("Fin de la démonstration du polymorphisme.")