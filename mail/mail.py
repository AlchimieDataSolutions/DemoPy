import adsToolBox as ads


logger = ads.Logger(logLevel = ads.Logger.DEBUG, logger_name="mon_logger")
MonMail = mail(dictionnary={"clientId":"",
                  "clientSecret":"",
                  "url":"",
                  "email":"",
                  "scope":"",
                  "server":""},
                logger=logger)

MonMail.connect_with_token()
data = MonMail.get_email(mailbox="INBOX",readonly=True,emailFrom="chavegrandn@chavegrand.com")
if data:
    for element in data:
        content=MonMail.read_email(element,get_attachment=True)
        print(content)
        break

MonMail.logout()