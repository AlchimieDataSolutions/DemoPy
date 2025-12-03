import utils
import os
import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")

"""
Pour une première connexion suivre la procédure : 
https://developers.google.com/calendar/api/quickstart/python?authuser=1&hl=fr

sections : "Activer l'API", "Accéder à l'écran de consentement OAuth", "Accéder à "Identifiants""

le paramètre "token_file" de la classe "GoogleCalendarConnector" ne doit être renseigné qu'après une deuxième connexion.
Le fichier contenant le token est créé lors de la première connexion.
"""

google_calender = ads.GoogleCalendarConnector({
    "calendar_ids": ["antoine.ducoulombier@alchimiedatasolutions.com"],
    "token_file": "token.json",
    "credentials_file": "demo_creds.json"
}, logger=logger)

google_calender.connect()
google_calender.save_events_to_csv(google_calender.get_events(),"events.csv")