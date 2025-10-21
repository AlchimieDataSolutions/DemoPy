import os
import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
env = ads.env(logger)

from_addr = env.MAIL_FROM if hasattr(env, 'MAIL_FROM') else None

# Déclaration du reader
mailReader = ads.mail({
    "url": env.MAIL_URL,
    "clientId": env.MAIL_CLIENT_ID,
    "clientSecret": env.MAIL_CLIENT_SECRET,
    "email": env.MAIL,
    "scope": "https://outlook.office365.com/.default",
    "server": "outlook.office365.com"
}, logger, 'oauth2')

# On va lire les mails non lus de la boîte principale de la part d'un interlocuteur
email_ids = mailReader.get_email(
    mailbox="INBOX", # Boîte principale
    readonly=True, # On va seulement lire
    emailFrom=from_addr, # Filtre sur l'interlocuteur
    emailSubject=None, # Filtre sur l'objet
    flag="UNSEEN", # Filtre sur l'état du mail
    charset='US-ASCII' # encodage
)

print(f"{len(email_ids)} emails non lus")

# Lisons le premier mail
email_id = email_ids[0]
email_content = mailReader.read_email(email_id, get_attachment=True)
print(f"📩 Contenu du mail:\n{email_content['message']}")
if "attachement" in email_content:
    for attachement in email_content["attachement"]:
        print(f"Pièce jointe: {attachement['filename']}")
# mailReader.mark_as_seen(email_id) # Met le mail en lu
# mailReader.mark_as_un_seen(email_id) # Met le mail en non lu
# mailReader.delete(email_id) # Met le mail dans la corbeille
mailReader.logout()