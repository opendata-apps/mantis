import smtplib
import os
import datetime


from app.config import Config

# Variablen für die Emails
# art = "Katze"


def send_email(subject="no subject", content="no content", to="test@example.com"):
    """ Send a simple, stupid, text, UTF-8 mail in Python """

    for ill in ["\n", "\r"]:
        subject = subject.replace(ill, ' ')

    headers = {
        'Content-Type': 'text; charset=utf-8',
        'Content-Disposition': 'inline',
        'Content-Transfer-Encoding': '8bit',
        'From': "mantis@example.com",
        'To': to,
        'Date': datetime.datetime.now().strftime('%a, %d %b %Y  %H:%M:%S %Z'),
        'X-Mailer': 'python',
        'Subject': subject
    }

    # create the message
    msg = ''
    for key, value in headers.items():
        msg += "%s: %s\n" % (key, value)

    # add contents
    msg += f"{content}"

    s = smtplib.SMTP(Config.host, Config.port)

    if Config.tls:
        s.ehlo()
        s.starttls()
        s.ehlo()

    if Config.username and Config.password:
        s.login(Config.username, Config.password)
    s.sendmail(headers['From'], headers['To'], msg.encode("utf8"))
    s.quit()