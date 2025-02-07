from CommonLib import *

mailReader = ads.mail({
    "url": env.MAIL_URL,
    "clientId": env.MAIL_CLIENT_ID,
    "clientSecret": env.MAIL_CLIENT_SECRET,
    "email": env.MAIL,
    "scope": "https://outlook.office365.com/.default",
    "server": "outlook.office365.com",
}, logger, 'oauth2')

email_ids = mailReader.get_email(mailbox="INBOX", readonly=True, emailFrom=env.MAIL_FROM, flag="UNSEEN")

print(f"{len(email_ids)} emails non lus de {env.MAIL_FROM}")

if email_ids:
    email_id = email_ids[0]
    email_content = mailReader.read_email(email_id, get_attachment=True)
    print(f"📩 Contenu du mail:\n{email_content['message']}")
    if "attachement" in email_content:
        for attachement in email_content["attachement"]:
            print(f"Pièce jointe: {attachement['filename']}")
    mailReader.mark_as_seen(email_id)
    mailReader.mark_as_un_seen(email_id)
    mailReader.delete(email_id)
mailReader.logout()