from app.config import Config
import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(subject="no subject",
               text="no content",
               html="no content",
               to="test@example.com"):
    """ Send a multipart email """

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = Config.sender_email
    message["To"] = to

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)

    context = ssl.create_default_context()
    with smtplib.SMTP(Config.host, Config.port) as server:
        server.starttls(context=context)
        server.login(Config.sender_email, Config.sender_pass)
        server.sendmail(Config.sender_email, to, message.as_string())
