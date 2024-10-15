import adsToolBox as ads

import time
import logging
import os
import threading

logger = ads.Logger(None, logging.INFO, "AdsLogger")
logger.info("Début de la démonstration...")

# On active le timer, les requêtes seront chronométrées
ads.set_timer(True)

file_path = "test.txt"
if os.path.exists(file_path):
    os.remove(file_path)

# On va simuler la reception/création du fichier après 5 secondes
def create_file_with_delay(file_path, delay, logger):
    logger.info(f"Création du fichier dans {delay} secondes...")
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
