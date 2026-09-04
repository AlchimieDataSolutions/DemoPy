"""
OdooConnector : accès XML-RPC à Odoo.

Aucun extra nécessaire : OdooConnector n'utilise que xmlrpc.client, du
module standard. C'est le seul connecteur externe de la toolbox qui ne
demande rien de plus que le cœur.
"""
import os

import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
env = ads.Env(logger=logger)

# ---------------------------------------------------------------------------
# 1. Instanciation
# ---------------------------------------------------------------------------
# Les cinq clés sont TOUTES obligatoires. Contrairement aux classes Db* qui
# utilisent dictionnary.get(), OdooConnector lit dictionnary["clé"] : une clé
# absente lève un KeyError dès l'instanciation, avant toute connexion.
# C'est plus sûr, et l'erreur est immédiate.
odoo = ads.OdooConnector(
    {
        "name": "Odoo Connection",   # libellé libre, sert à __str__ et aux logs
        "url": env.ODOO_URL,         # racine du serveur, sans /xmlrpc
        "user": env.ODOO_USER,
        "password": env.ODOO_PWD,
        "db": env.ODOO_DB,
    },
    logger=logger,
)

# __str__ renvoie "Connexion Odoo: <name>" : pratique dans un log de suivi
# quand plusieurs instances Odoo coexistent.
print(odoo)

# ---------------------------------------------------------------------------
# 2. Connexion
# ---------------------------------------------------------------------------
# connect() s'authentifie et récupère un uid. Deux cas d'échec, tous deux
# transformés en RuntimeError après journalisation en ERROR :
#   - identifiants refusés (uid falsy) ;
#   - erreur de transport XML-RPC (URL fausse, serveur injoignable).
# L'uid obtenu est tracé en DEBUG.
odoo.connect()

# ---------------------------------------------------------------------------
# 3. desc : le schéma d'un modèle
# ---------------------------------------------------------------------------
# Renvoie la description des champs du modèle. Indispensable avant un get(),
# car les noms de champs Odoo ne correspondent pas aux libellés de
# l'interface web.
fields = odoo.desc(table="account.account")
logger.info(f"Descriptions: {fields}")

# ---------------------------------------------------------------------------
# 4. get : lire des enregistrements
# ---------------------------------------------------------------------------
# Trois arguments, tous obligatoires :
#   table  : le modèle Odoo, avec des points ("hr.employee")
#   fields : les champs à ramener. Une liste vide ramènerait TOUT, ce qui est
#            coûteux : listez explicitement ce dont vous avez besoin.
#   filtre : un domaine Odoo, c'est-à-dire une liste de triplets
#            [champ, opérateur, valeur]. Une liste vide = aucun filtre.
values = odoo.get(
    table="hr.employee",
    fields=["id", "name", "work_email"],
    filtre=[],
)
logger.info(f"Valeurs: {values}")

# Exemples de domaines Odoo. La syntaxe est propre à Odoo, pas du SQL :
#   [["active", "=", True]]
#   [["name", "ilike", "dupont"]]
#   [["id", "in", [1, 2, 3]]]
#   [["create_date", ">=", "2026-01-01"]]
# Plusieurs triplets sont combinés en ET implicite.
actifs = odoo.get(
    table="hr.employee",
    fields=["id", "name"],
    filtre=[["active", "=", True]],
)
logger.info(f"{len(actifs)} employé(s) actif(s)")

# get renvoie une liste de DICTIONNAIRES, pas de tuples — contrairement à
# sql_query des classes Db*. Pour alimenter un Pipeline depuis Odoo, il faut
# donc convertir en listes de valeurs dans l'ordre des colonnes cibles.

# ---------------------------------------------------------------------------
# 5. put : créer des enregistrements
# ---------------------------------------------------------------------------
# put renvoie la liste des IDS créés par Odoo, à conserver si vous devez
# rapprocher les lignes insérées de votre source.
ids = odoo.put(
    table="MaTable",
    lines=[
        ("1", "employe1", "data engineer"),
        ("2", "employe2", "data analyst"),
    ],
)
logger.info(f"Identifiants créés : {ids}")

# Attention : put crée, il ne met pas à jour. Il n'y a pas d'upsert côté
# OdooConnector pour le moment. Pour modifier un enregistrement existant,
# il faut passer par l'API Odoo directement.