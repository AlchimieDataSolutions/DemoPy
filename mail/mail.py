import adsToolBox as ads


logger = ads.Logger(logLevel = ads.Logger.DEBUG, logger_name="mon_logger")
MonMail = mail(dictionnary={"clientId":"d01021f8-4d0d-4371-a2a8-df64a370f432",
                  "clientSecret":"REMOVED_SECRET",
                  "url":"https://login.microsoftonline.com/7638e353-5319-43ae-b3d3-2ac7fd0ac61f/oauth2/v2.0/token",
                  "email":"echange@terralacta.com",
                  "scope":"https://outlook.office365.com/.default",
                  "server":"outlook.office365.com"},
                logger=logger)

MonMail.connect_with_token()
data = MonMail.get_email(mailbox="INBOX",readonly=True,emailFrom="chavegrandn@chavegrand.com")
if data:
    for element in data:
        content=MonMail.read_email(element,get_attachment=True)
        print(content)
        break

MonMail.logout()