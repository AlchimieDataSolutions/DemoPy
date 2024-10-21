from adsToolBox import OdooConnector
from CommonLib import *

#Création de l'objet Odoo
odoo=OdooConnector({"name":"Odoo Connection", "url":env.ODOO_URL,
                    "user":env.ODOO_USER, "password":env.ODOO_PWD,"db":env.ODOO_DB}, logger=logger)

#Connexion
odoo.connect()

#Récupérer le schéma d'une table
fields = odoo.desc("account.account")
logger.info(f"Descriptions: {fields}")

#Récupérer les valeurs d'une tables en précisant les colonnes et un filtre
values = odoo.get("hr.employee", ['id', 'name', 'resource_id', 'user_id', 'work_email'], [])
logger.info(f"Valeurs: {values}")

#Insérer des lignes dans une table
odoo.put("MaTables",[("1","employe1","data engineer"),("2","employe2","data analyst")])