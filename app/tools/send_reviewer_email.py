import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from flask import current_app
from email.utils import make_msgid
from email.utils import formatdate
from email.header import Header


def rendertextmsg(md):

    return f"""
    Liebe Mantis-Freundin, lieber Mantis-Freund,

    Vielen Dank, dass Sie sich am Gottesanbeterinnen-Monitoring
    beteiligt haben. Wir haben Ihre Fundmeldung überprüft. In der
    unten angeführten Tabelle sind alle Daten zu ihrer Meldung sowie
    die Bestimmung des Geschlechtes/ Stadiums aufgeführt. Mit der
    Überprüfung Ihres Fundes erscheint Ihr Punkt unter Auswertungen
    in der Verbreitungskarte. Aktuell liegen uns aus fast allen
    Landkreisen Meldungen vor. Nachdem die Art anfänglich vor allem
    im Süden zu finden war, dringt sie nun weiter in Richtung Norden
    vor. In den nördlichen Landkreisen sind Meldungen noch selten. Es
    gibt aber auch in allen Landkreisen noch Nachweislücken. Auch in
    Berlin und Potsdam mehren sich die Funde.

    Noch einmal vielen Dank für Ihre Meldung.

    Mit freundlichen Grüßen

    Ihr Team vom Mantis-Portal

    Folgende Daten haben wir erhalten:
    ==================================
    Kontakt: {md['user_kontakt']}

    {'Latitude:':<21}  {md['latitude']:>22}
    {'Longitude:':<21}  {md['longitude']:>22}
    {'PLZ:':<21}  {str(md['plz']):>22}
    {'Ort:':<21}  {md['ort']:>22}
    {'Straße:':<21}  {md['strasse']:>22}
    {'Bundesland:':<21} {md['land']:>22}
    {'Kreis:':<21} {md['kreis']:>22}
    {'Funddatum:':<21} {md['datum']:>22}

    ==========

    Folgendes Geschlecht bzw. Entwicklungsstadium wurden festgestellt:

    (siehe auch:  https://gottesanbeterin-gesucht.de/bestimmung)

    {'Männchen:':<10} {str(md['art_m']) + " ":10}
    {'Weibchen:':<10} {str(md['art_w']) + " ":<10}
    {'Nymphe(n):':<10} {str(md['art_n']) + " ":<10}
    {'Oothek(n):':<10} {str(md['art_o']) + " ":<10}
    {md['anm_bearbeiter']}

    Ihr Link für neue Meldungen:
    https://gottesanbeterin-gesucht.de/report/{md['user_id']}

    WICHTIGER HINWEIS:

    - Behandeln Sie den Link wie ein Passwort!
    - Publizieren Sie den Link nicht in Foren, Messengern, ...
    """.format(md)


def renderhtmlmsg(md):

    return f"""
    <h3>Liebe Mantis-Freundin, lieber Mantis-Freund,</h3>
    <p>
    Vielen Dank, dass Sie sich am Gottesanbeterinnen-Monitoring
    beteiligt haben. Wir haben Ihre Fundmeldung überprüft. In der
    unten angeführten Tabelle sind alle Daten zu ihrer Meldung sowie
    die Bestimmung des Geschlechtes/ Stadiums aufgeführt. Mit der
    Überprüfung Ihres Fundes erscheint Ihr Punkt unter Auswertungen
    in der Verbreitungskarte. Aktuell liegen uns aus fast allen
    Landkreisen Meldungen vor. Nachdem die Art anfänglich vor allem
    im Süden zu finden war, dringt sie nun weiter in Richtung Norden
    vor. In den nördlichen Landkreisen sind Meldungen noch selten. Es
    gibt aber auch in allen Landkreisen noch Nachweislücken. Auch in
    Berlin und Potsdam mehren sich die Funde.
    </p>
    <p>
    Noch einmal vielen Dank für Ihre Meldung.
    </p>
    <p>
    Mit freundlichen Grüßen
    </p>
    <p>
    Ihr Team vom Mantis-Portal
    </p>
    <hr/>
    <p><b>Folgende Daten haben wir erhalten:</b></p>
    <table>
    <tr>
    <td>Kontakt:</td><td>{md['user_kontakt']}</td>
    </tr>
    <tr>
    <td>Latitude</td>
    <td>{md['latitude']}</td>
    </tr>
    <tr>
    <td>Longitude</td>
    <td>{md['longitude']}</td>
    </tr>
    <tr>
    <td>PLZ</td>
    <td>{md['plz']}</td>
    </tr>
    <tr>
    <td>Ort</td>
    <td>{md['ort']}</td>
    </tr>
    <tr>
    <td>Straße</td>
    <td>{md['strasse']}</td>
    </tr>
    <tr>
    <td>Bundesland</td>
    <td>{md['land']}</td>
    </tr>
    <tr>
    <td>Kreis</td>
    <td>{md['kreis']}</td>
    </tr>
    <tr>
    <td>Funddatum</td>
    <td>{md['datum']}</td>
    </tr>
    <tr>
    <td colspan="2">
    <b>Folgendes Geschlecht bzw. Entwicklungsstadium wurden festgestellt:</b>
    </td>
    </tr>
    <tr>
    <td colspan="2">
    (siehe auch:  https://gottesanbeterin-gesucht.de/bestimmung)
    </td>
    </tr>
    <tr>
    <td>
    Männchen:
    </td>
    <td>
    {md['art_m']}
    </td>
    </tr>
    <tr>
    <td>
    Weibchen
    </td>
    <td>
    {md['art_w']}
    </td>
    </tr>
    <tr>
    <td>
    Nymphe(n)
    </td>
    <td>
    {md['art_n']}
    </td>
    </tr>
    <tr>
    <td>
    Oothek(n)
    </td>
    <td>
    {md['art_o']}
    </td>
    </tr>
    <tr>
    <td colspan="2">
    {md['anm_bearbeiter']}
    </td>
    </tr>
    <tr>
    <td>Ihr Link für weitere Meldungen</td>
    <td></td>
    </tr>
    <tr>
    <td colspan="2">
      https://gottesanbeterin-gesucht.de/report/{md['user_id']}
    </td>
    </tr>
    <tr>
     <td><b>WICHTIGER HINWEIS:</b></td>
     <td></td>
    </tr>
    <tr>
     <td colspan="2">
       <ol>
         <li>Behandeln Sie den Link wie ein Passwort</li>
         <li>Publizieren Sie den Link nicht in Foren, Messengern, ...</li>
       </ol>
     <td>
    </tr>
    </table>
    """.format(md)


def send_email(data):
    """ Send a multipart email """

    # Generate Message-ID
    msgid = make_msgid()

    md = data
    text = ""
    if md['anm_bearbeiter']:
        if md['anm_bearbeiter'] == '':
            text = 'Keine Anmerkung(en) vom Reviewer.'
        else:
            text = 'Anmerkung(en) vom Reviewer: ' + md['anm_bearbeiter']
    md['anm_bearbeiter'] = text
    md['datum'] = md['dat_fund_von'].strftime(' %d.%m.%Y')
    text = rendertextmsg(md)
    html = renderhtmlmsg(md)
    subject = "Meldebestätigung"
    smtp_server = current_app.config.get('host', '')
    login = current_app.config.get('sender_email', '')  # paste your login generated by Mailtrap
    password = current_app.config.get('sender_pass', '')  # paste your password generated by Mailtrap

    sender_email = current_app.config.get('sender_email', '')
    user_name = md['user_name']
    receiver_email = md['user_kontakt']
    message = MIMEMultipart("alternative")
    message["Subject"] = str(Header(subject, 'utf-8'))
    message["From"] = formataddr(('Gottesanbeterin gesucht',
                                  current_app.config.get('sender_email', '')))
    message["To"] = formataddr((user_name, receiver_email))
    message["MIME-Version"] = "1.0"
    
    # Set the Message-ID and Date headers correctly
    message["Message-ID"] = msgid
    message["Date"] = formatdate(localtime=True)
    
    # Add Reply-To header
    message["Reply-To"] = current_app.config.get('sender_email', '')

    text = rendertextmsg(data)
    html = renderhtmlmsg(data)

    # Convert both parts to MIMEText objects with UTF-8 encoding
    # and add them to the MIMEMultipart message
    part1 = MIMEText(text, "plain", "utf-8")
    part2 = MIMEText(html, "html", "utf-8")
    message.attach(part1)
    message.attach(part2)
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(smtp_server, current_app.config.get('port', 25)) as server:
            server.starttls(context=context)
            server.login(login, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
    except Exception as ex:
        raise ex
