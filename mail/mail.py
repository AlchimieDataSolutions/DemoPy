# adstoolbox[files]
"""
MailReader : lecture IMAP et pièces jointes.

MailReader lui-même ne demande AUCUN extra : il n'utilise que imaplib,
email et requests, tous dans le cœur. L'extra files n'est nécessaire que
pour la section 5, qui enregistre les pièces jointes avec FileHandler.
"""
import os

import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
env = ads.Env(logger=logger)

# ---------------------------------------------------------------------------
# 1. Deux modes d'authentification
# ---------------------------------------------------------------------------
# auth_mode est le TROISIÈME argument positionnel, obligatoire : 'oauth2' ou
# 'credentials'. Toute autre valeur lève un ValueError.
#
# Point important : la connexion est établie DANS __init__. Il n'y a pas de
# méthode connect() comme sur les classes Db*. Instancier, c'est se
# connecter — et donc échouer tout de suite si les identifiants sont faux.
#
# Les clés du dictionnaire dépendent du mode, et sont toutes lues via .get()
# donc une clé absente vaut None sans erreur immédiate :
#
#   oauth2       url, clientId, clientSecret, scope, server, email
#   credentials  server, login, password, email
mr = ads.MailReader(
    {
        "url": env.MAIL_URL,                   # https://login.microsoftonline.com/...
        "clientId": env.MAIL_CLIENT_ID,
        "clientSecret": env.MAIL_CLIENT_SECRET,
        "email": env.MAIL,                     # ads@toolbox.com
        "scope": "https://outlook.office365.com/.default",
        "server": "outlook.office365.com",
    },
    logger,
    "oauth2",
)

# En mode credentials, la configuration serait :
#
#   ads.MailReader(
#       {
#           "server": "imap.exemple.fr",
#           "login": env.MAIL_LOGIN,
#           "password": env.MAIL_PWD,
#           "email": env.MAIL,
#       },
#       logger,
#       "credentials",
#   )

# ---------------------------------------------------------------------------
# 2. get_email : chercher des identifiants de messages
# ---------------------------------------------------------------------------
# Renvoie une liste d'IDENTIFIANTS, pas de messages. Le contenu se lit
# ensuite avec read_email, un identifiant à la fois.
email_ids = mr.get_email(
    mailbox="INBOX",             # dossier IMAP ; "Sent", "Archive"...
    email_from=env.get(item="MAIL_FROM", default=None),
    email_subject=None,          # filtre sur l'objet, None => pas de filtre
    flag="UNSEEN",               # état du message
    charset="US-ASCII",          # encodage de la requête IMAP
    readonly=True,               # keyword-only
)

# readonly=True ouvre la boîte en lecture seule : parcourir les messages ne
# les marque PAS comme lus. C'est le réglage à privilégier pour un traitement
# qui doit pouvoir être rejoué. readonly=False (défaut) laisse le serveur
# marquer les messages lus au fil de la lecture.
#
# flag accepte dix valeurs, insensibles à la casse :
#   ALL, SEEN, UNSEEN, FLAGGED, UNFLAGGED, ANSWERED, UNANSWERED,
#   DELETED, UNDELETED, DRAFT
# Toute autre valeur lève un ValueError qui liste les valeurs admises.

print(f"{len(email_ids)} email(s) correspondant au filtre")

# La liste peut être VIDE : indexer email_ids[0] sans vérifier lève un
# IndexError. C'est le cas courant sur une boîte sans message non lu.
if not email_ids:
    logger.warning("Aucun message à traiter, fin du script.")
    mr.logout()
    raise SystemExit(0)

# ---------------------------------------------------------------------------
# 3. read_email : le contenu d'un message
# ---------------------------------------------------------------------------
email_id = email_ids[0]
email_content = mr.read_email(
    email_id,
    get_attachment=True,   # keyword-only ; False par défaut
)

# Le retour est un dictionnaire. La clé 'message' contient le corps décodé,
# la clé 'attachment' n'est présente QUE si get_attachment=True et qu'il y a
# effectivement des pièces jointes — d'où le test d'appartenance plus bas.
print(f"Contenu du mail :\n{email_content['message']}")

# Le décodage du corps gère les messages multipart et les encodages
# exotiques via chardet : c'est ce qui justifie la présence de chardet dans
# le cœur de la toolbox.

# ---------------------------------------------------------------------------
# 4. Marquer et supprimer
# ---------------------------------------------------------------------------
# Trois méthodes, chacune sur un identifiant unique. Elles n'ont d'effet que
# si la boîte a été ouverte en écriture, donc pas après un readonly=True.
#
# mr.mark_as_seen(e_id=email_id)      marque comme lu
# mr.mark_as_un_seen(e_id=email_id)   remet en non lu
# mr.delete(e_id=email_id)            déplace vers la corbeille
#
# delete ne supprime pas définitivement : le message part à la corbeille du
# serveur. Une purge éventuelle reste à faire côté messagerie.

# ---------------------------------------------------------------------------
# 5. Enregistrer les pièces jointes
# ---------------------------------------------------------------------------
# adstoolbox[files] à partir d'ici.
local_f = ads.FileHandler(logger=logger)

if "attachment" in email_content:
    for attachement in email_content["attachment"]:
        print(f"Pièce jointe : {attachement['filename']}")
        # write_file attend un ITÉRABLE de contenus, d'où les crochets : une
        # chaîne nue serait parcourue caractère par caractère.
        local_f.write_file(
            file_path=attachement["filename"],
            content=[attachement["content"]],
            mode="wb",
        )

# Le nom de fichier vient du message : il n'est ni nettoyé ni vérifié. Un
# expéditeur malveillant pourrait proposer "../../etc/passwd". En
# production, forcez le répertoire de destination et ne gardez que le nom
# de base :
#
#   nom = os.path.basename(attachement["filename"])
#   local_f.write_file(file_path=f"pieces_jointes/{nom}", content=[...], mode="w")

# ---------------------------------------------------------------------------
# 6. Fermer la session
# ---------------------------------------------------------------------------
# logout() libère la connexion IMAP. Sans lui, le serveur garde la session
# ouverte jusqu'à son propre délai d'expiration, et certains fournisseurs
# limitent le nombre de sessions simultanées.
mr.logout()