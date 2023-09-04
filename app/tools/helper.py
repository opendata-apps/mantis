import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(subject, body, recipient):
    sender = 'email'
    password = 'pass'

    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = sender
    message['To'] = recipient

#     # Attach the plain text body
    html_body = f"""\
<html>
  <head>
    <style>
      @media only screen and (max-width: 600px) {{
        .container {{width: 100% !important;}}
      }}
      body {{background-color: #f2f2f2; font-family: Arial, sans-serif;}}
      .container {{background-color: #ffffff; padding: 20px; border-radius: 10px; margin: auto; max-width: 600px;}}
      .logo {{display: block; margin: auto; width: 200px;}}
      .header {{text-align: center; margin-top: 30px; font-size: 24px; color: #333;}}
      .text {{text-align: justify; font-size: 16px; line-height: 1.5; color: #666;}}
      .footer {{text-align: justify; font-size: 14px; margin-top: 30px; color: #999;}}
      .image {{display: block; margin: auto; width: 400px; margin-top: 30px;}}
      .button {{display: inline-block; background-color: #057A55; color: #ffffff; padding: 10px 20px; border-radius: 5px; text-decoration: none; margin-top: 30px;}}
      .button:hover {{background-color: #057A55;}}
    </style>
  </head>
  <body>
    <div class="container">
      <img src="http://mantis.methopedia.eu/static/images/logo.png" alt="Mantis Logo" class="logo">
      <h1 class="header">Vielen Dank für Ihre Meldung!</h1>
      <p class="text">Liebe/r Mantis-Freund*In,</p>
      <p class="text">Vielen Dank, dass Sie sich am Gottesanbeterinnen-Monitoring beteiligt haben. Ihre Meldung ist bei uns eingegangen. Seit Projektbeginn wurde uns die Art xyz aus Brandenburg und Berlin gemeldet. Aus Brandenburg liegen schon viele Funde vor. Vor allem aus dem Süden unseres Bundeslandes. Im Norden wird die Art viel seltener gesichtet. Aus Berlin erhielten wir in den vergangenen Jahren vermehrt Meldungen quer über das Stadtgebiet verteilt. Um die Situation darstellen zu können, zählt für uns nach wie vor jede Meldung. Sobald wir Ihren Fund überprüft und freigegeben haben, wird er in der Verbreitungskarte angezeigt. Im Weiteren erhalten Sie dann noch die Information, ob es sich um eine Gottesanbeterin gehandelt hat oder um eine andere Art. Sollte Ihre Fundmeldung nicht aus Brandenburg und Berlin sein, geht sie aber auch nicht verloren. Wir nehmen Sie mit in unsere Datenbank auf und stehen im Kontakt mit Kolleg*Innen in anderen Bundesländern. In jedem Fall noch einmal vielen Dank für Ihre Meldung.</p>
      <p class="text">Mit freundlichen Grüßen</p>
      <p class="text">Ihr Team vom Mantis-Portal</p>
      <img src="http://mantis.methopedia.eu/static/images/mantisEat.jpg" alt="Mantis Eating" class="image">
      <a href="http://mantis.methopedia.eu" class="button">Zur Website</a>
      <p class="footer">Dies ist eine automatisch generierte E-Mail. Bitte antworten Sie nicht auf diese Nachricht.</p>
    </div>
  </body>
</html>
"""

    # Attach the HTML body to the email message
    message.attach(MIMEText(html_body, 'html'))

    # Attach any additional images to the email message (optional)
    # with open('path/to/image.jpg', 'rb') as image:
    #     img = MIMEImage(image.read())
    #     message.attach(img)

    # Send the email using SMTP
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender, password)
    server.sendmail(sender, recipient, message.as_string())
    server.quit()


# Example usage
send_email('Report Successful', '', 'email')
