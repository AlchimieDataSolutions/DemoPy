from adsToolBox import OdooConnector
from CommonLib import *


#Création de l'objet Odoo
odoo=OdooConnector({"name":"", "url":"", "user":"", "password":"","db":""},logger=logger)

#Connexion
odoo.connect()

#Récupérer le schéma d'une table
odoo.desc("MaTable")

#Récupérer les valeurs d'une tables en précisant les colonnes et un filtre
odoo.get("MaTable","MesChamps","MonFiltre")

#Insérer des lignes dans une table
odoo.put("MaTables",[("1","employe1","data engineer"),("2","employe2","data analyst")])