import adsGenericFunctions as ads

import time
from env import *
import logging
import psycopg2
import threading

# On établit une connexion pour le logger pour qu'il puisse écrire en base
logger_connection = psycopg2.connect(database=pg_dwh_db, user=pg_dwh_user, password=pg_dwh_pwd, port=pg_dwh_port,
                                     host=pg_dwh_host)
logger = ads.Logger(logger_connection, logging.INFO, "AdsLogger", "LOGS", "LOGS_details")
logger.info("Début de la démonstration...")

# On active le timer, les requêtes seront chronométrées
ads.set_timer(True)

file_path = "test.txt"
if os.path.exists(file_path):
    os.remove(file_path)

# Simuler la création du fichier après 5 secondes
def create_file_with_delay(file_path, delay, logger):
    time.sleep(delay)
    with open(file_path, 'w') as f:
        f.write("Fichier crée.")
    logger.info("Fichier crée par un autre processus")


threading.Thread(target=create_file_with_delay, args=(file_path, 5, logger)).start()
logger.info("Début de la recherche.")
if ads.wait_for_file(os.getcwd(), file_path, 10):
    logger.info("Fichier bien trouvé.")
else:
    logger.error("Pas de fichier trouvé.")

if os.path.exists(file_path):
    os.remove(file_path)
logger.info("Fin de la démonstration")

