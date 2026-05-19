import utils
import os
import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
env = ads.Env(logger)

from_addr = env.MAIL_FROM if hasattr(env, 'MAIL_FROM') else None

# Déclaration du reader
mr = ads.MailReader({
    "url": env.MAIL_URL, # https://login.microsoftonline.com/etc
    "clientId": env.MAIL_CLIENT_ID,
    "clientSecret": env.MAIL_CLIENT_SECRET,
    "email": env.MAIL, # ads@toolbox.com
    "scope": "https://outlook.office365.com/.default",
    "server": "outlook.office365.com"
}, logger, 'oauth2')

# On va lire les mails non lus de la boîte principale de la part d'un interlocuteur
email_ids = mr.get_email(
    mailbox = "INBOX", # Boîte principale
    readonly = True, # On va seulement lire et ne pas marquer en lu
    email_from = from_addr, # Filtre sur l'interlocuteur
    email_subject = None, # Filtre sur l'objet
    flag = "UNSEEN", # Filtre sur l'état du mail
    charset = 'US-ASCII' # encodage
)

print(f"{len(email_ids)} emails non lus")
exit()

# Lisons le premier mail
email_id = email_ids[0]
email_content = mr.read_email(
    email_id,
    get_attachment = True, # récupère aussi la pièce jointe
)
print(f"📩 Contenu du mail:\n{email_content['message']}")

local_f = ads.FileHandler(logger)

if "attachment" in email_content:
    for attachement in email_content["attachment"]:
        print(f"Pièce jointe: {attachement['filename']}")
        local_f.write_file(attachement['filename'], [attachement['content']])

# mailReader.mark_as_seen(email_id) # Met le mail en lu
# mailReader.mark_as_un_seen(email_id) # Met le mail en non lu
# mailReader.delete(email_id) # Met le mail dans la corbeille

mr.logout()