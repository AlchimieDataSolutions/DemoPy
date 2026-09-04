# adstoolbox[pgsql]
"""
Requêtes simples : sql_exec, sql_scalaire, find_text_anywhere.

Regroupe les anciens execute.py, fonction_scalaire.py et find_text.py :
les trois illustraient un aller-retour SQL sans batch ni pipeline.

Pour la lecture par batchs, voir operations/read.py.
"""
import os

import adsToolBox as ads

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

# ===========================================================================
# 1. sql_exec : exécuter sans rien attendre en retour
# ===========================================================================
# Pour le DDL (CREATE, DROP, ALTER, TRUNCATE) et le DML sans lecture
# (UPDATE, DELETE). Renvoie None : aucun moyen de savoir combien de lignes
# ont été affectées. Si le compte importe, faites suivre d'un
# sql_scalaire("SELECT COUNT(*) ...").
source.sql_exec(query="DROP TABLE IF EXISTS demo_insert;")
source.sql_exec(query="""
CREATE TABLE IF NOT EXISTS demo_insert (
    id SERIAL PRIMARY KEY,
    tenantname VARCHAR(255),
    fichier VARCHAR(255)
);""")

# Plusieurs instructions dans un même appel fonctionnent sur PostgreSQL et
# MySQL, mais ce n'est pas portable : le comportement dépend du driver.
# Préférez un appel par instruction si le code doit tourner sur les trois
# backends.
source.sql_exec(query="""
INSERT INTO demo_insert (tenantname, fichier) VALUES ('T1', 'a.csv');
INSERT INTO demo_insert (tenantname, fichier) VALUES ('T2', 'b.csv');
""")

# ===========================================================================
# 2. sql_scalaire : une seule valeur
# ===========================================================================
# Renvoie la PREMIÈRE colonne de la PREMIÈRE ligne. Idéal pour un COUNT, un
# MAX, un NOW() ou un test d'existence.
print(source.sql_scalaire(query="SELECT NOW()"))
print(source.sql_scalaire(query="SELECT COUNT(*) FROM demo_insert;"))

# ATTENTION : plusieurs champs demandés, seul le premier revient. Le second
# est silencieusement perdu — aucun avertissement.
print(source.sql_scalaire(query="SELECT 1, NOW()"))

# Sur un résultat vide, sql_scalaire renvoie None. Un None peut donc
# signifier « aucune ligne » comme « la valeur trouvée est NULL » : les deux
# cas sont indiscernables. Si la distinction compte, passez par sql_query.
print(source.sql_scalaire(query="SELECT tenantname FROM demo_insert WHERE 1=0"))

# ===========================================================================
# 3. find_text_anywhere : chercher une valeur partout
# ===========================================================================
# Parcourt toutes les colonnes TEXTUELLES de toutes les tables de tous les
# schémas. Outil de diagnostic — « où est stockée cette valeur ? » — pas un
# outil de production : le coût croît avec la taille de la base.
results = source.find_text_anywhere(
    search="User1%",         # motif SQL LIKE : % et _ sont des jokers
    schema=None,             # None => tous les schémas
    table=None,              # None => toutes les tables
    log_every=50,            # journalise la progression toutes les 50 colonnes
    include_views=False,     # les vues sont exclues par défaut
)

# Le retour est une liste de dictionnaires à cinq clés.
for result in results:
    print(
        f"trouvé {result['count']} fois dans "
        f"{result['schema']}.{result['table']}.{result['column']}"
        f" — requête : {result['query']}",
    )

# La clé 'query' contient une requête prête à l'emploi pour retrouver les
# lignes concernées : c'est le principal intérêt du retour.
#
# Restreindre la recherche change tout en performance. Sur une base
# volumineuse, ciblez toujours un schéma :
resultats_cibles = source.find_text_anywhere(
    search="User1%",
    schema="public",
    table="demo_insert",
    log_every=10,
    include_views=True,   # inclut aussi les vues
)

logger.info(f"{len(resultats_cibles)} correspondance(s) sur la cible restreinte")

# Seules les colonnes de type texte sont inspectées : chercher un nombre ou
# une date ne donnera rien, même si la valeur existe dans une colonne
# numérique. Convertissez la colonne côté SQL si besoin.

source.disconnect()