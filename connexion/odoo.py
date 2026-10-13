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

# Le retour est volumineux : plusieurs centaines de champs sur un modèle
# standard, chacun avec son libellé, son type et parfois son aide. Le
# journaliser entier rend la sortie illisible — on échantillonne.
logger.info(f"{len(fields)} champ(s) décrits sur account.account")
for nom, meta in list(fields.items())[:5]:
    logger.info(f"  {nom} : {meta['type']} — {meta['string']}")

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

# PIÈGE : un champ vide ne vaut ni None ni "" mais False. C'est la
# convention XML-RPC d'Odoo, et elle traverse telle quelle :
#
#   {"id": 25, "name": "Matthieu Vannin", "work_email": False}
#
# Un `email.lower()` sur une telle valeur lève AttributeError, et insérer ce
# False dans une colonne texte donne "false" ou 0 selon le backend.
# Normalisez avant de transmettre :
for ligne in values:
    if ligne.get("work_email") is False:
        ligne["work_email"] = None

# ---------------------------------------------------------------------------
# 5. put : créer des enregistrements
# ---------------------------------------------------------------------------
# Chaque élément de `lines` est transmis tel quel à la méthode `create`
# d'Odoo, qui attend un DICTIONNAIRE {champ: valeur}. Des tuples ou des
# listes de valeurs ne fonctionnent pas : les noms de champs sont
# obligatoires, Odoo n'ayant pas d'ordre de colonnes.
#
# put renvoie la liste des IDS créés, à conserver si vous devez rapprocher
# les lignes insérées de votre source.
#
# Cet appel est commenté : il écrirait réellement dans votre instance Odoo.
# Décommentez-le en remplaçant le modèle et les champs par les vôtres, après
# un desc() pour connaître les noms exacts.
#
# ids = odoo.put(
#     table="hr.employee",
#     lines=[
#         {"name": "Employé de test", "work_email": "test@example.com"},
#     ],
# )
# logger.info(f"Identifiants créés : {ids}")

# Un modèle inexistant échoue côté serveur, pas à l'appel :
#   xmlrpc.client.Fault: <Fault 2: "Object MaTable doesn't exist">
# L'erreur est journalisée en ERROR puis propagée.

# Attention : put crée, il ne met pas à jour. Il n'y a pas d'upsert côté
# OdooConnector pour le moment. Pour modifier un enregistrement existant,
# il faut passer par l'API Odoo directement.