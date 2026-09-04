# adstoolbox[google]
"""
GoogleCalendarConnector : lecture d'agendas et export CSV.

Première connexion : suivre la procédure officielle
https://developers.google.com/calendar/api/quickstart/python?hl=fr
sections « Activer l'API », « Écran de consentement OAuth », « Identifiants ».

Le fichier credentials_file est celui téléchargé depuis la console Google.
Le fichier token_file, lui, est CRÉÉ par la première connexion : il n'existe
pas encore au premier lancement, et c'est normal.
"""
import os

import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")

# ---------------------------------------------------------------------------
# 1. Instanciation : une clé obligatoire, trois optionnelles
# ---------------------------------------------------------------------------
google_calendar = ads.GoogleCalendarConnector(
    {
        # OBLIGATOIRE (lu en dictionnary["calendar_ids"], donc KeyError si
        # absent). Une liste, même pour un seul agenda : get_events itère
        # dessus et renvoie un dictionnaire indexé par identifiant.
        "calendar_ids": ["antoine.ducoulombier@alchimiedatasolutions.com"],

        # Optionnel, défaut "token.json". Créé à la première connexion,
        # relu ensuite pour éviter de repasser par le navigateur.
        "token_file": "token.json",

        # Optionnel, défaut "credentials.json". Vient de la console Google.
        "credentials_file": "demo_creds.json",

        # Optionnel, et c'est le paramètre le plus important à connaître.
        # Le défaut est calendar.readonly : en LECTURE SEULE. Toute
        # tentative d'écriture échouera en 403 tant que ce scope n'est pas
        # élargi. Le connecteur n'expose de toute façon aucune méthode
        # d'écriture, donc le défaut convient à son usage.
        "scopes": ["https://www.googleapis.com/auth/calendar.readonly"],
    },
    logger=logger,
)

# __str__ liste les agendas surveillés.
print(google_calendar)

# ---------------------------------------------------------------------------
# 2. Connexion OAuth2
# ---------------------------------------------------------------------------
# Au premier appel, un navigateur s'ouvre pour le consentement, puis
# token_file est écrit. Aux appels suivants le token est relu, et rafraîchi
# automatiquement s'il a expiré.
#
# Conséquence pratique : ce connecteur ne convient pas tel quel à un job
# planifié sur un serveur sans navigateur, sauf si token_file a été généré
# au préalable sur un poste et déposé à côté du script.
google_calendar.connect()

# ---------------------------------------------------------------------------
# 3. get_events : deux limites à connaître
# ---------------------------------------------------------------------------
# max_results vaut 10 PAR DÉFAUT et s'applique PAR AGENDA. Sur un agenda
# chargé, la valeur par défaut ne ramène presque rien : c'est la première
# cause de « il me manque des événements ».
#
# Et le connecteur passe timeMin=maintenant : seuls les événements À VENIR
# sont retournés. Il n'y a pas de paramètre pour remonter dans le passé.
events = google_calendar.get_events(
    max_results=50,
)

# Les événements récurrents sont éclatés en occurrences individuelles
# (singleEvents=True) et triés par date de début (orderBy="startTime").

# Le retour est un dictionnaire {identifiant_agenda: [événements]}. Le
# nombre récupéré par agenda est journalisé en INFO.
for agenda, liste in events.items():
    logger.info(f"{agenda} : {len(liste)} événement(s)")

# ---------------------------------------------------------------------------
# 4. save_events_to_csv
# ---------------------------------------------------------------------------
# Écrit les événements dans un CSV via Polars — d'où la présence de polars
# dans l'extra google.
google_calendar.save_events_to_csv(
    events_data=events,
    csv_filename="events.csv",   # défaut : "calendar_events.csv"
)

# Le chemin est relatif au RÉPERTOIRE COURANT, pas au script : lancé depuis
# la racine du dépôt, le fichier apparaît à la racine, pas dans connexion/.
# Donnez un chemin absolu si l'emplacement importe.
logger.info(f"CSV écrit dans : {os.path.abspath('events.csv')}")

# Enchaîner les deux appels en une ligne, comme
#   save_events_to_csv(get_events(), "events.csv")
# fonctionne, mais empêche d'inspecter ou de filtrer les événements entre
# les deux. Gardez la variable intermédiaire.