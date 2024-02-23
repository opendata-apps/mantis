# import the necessary components first
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.config import Config
from datetime import datetime

def rendertextmsg(data):
    md = data.json
    if md['anm_bearbeiter'] =='':
        text = 'Keine Anmerkung(en) vom Reviewer.'
    else:
        text = 'Anmerkung(en) vom Reviewer: ' + md['anm_bearbeiter']
    md['anm_bearbeiter'] = text
    datum = md['dat_fund_von'].split(' ')[1:4]
    md['formdat'] = f"{datum[0]}. {datum[1]}. {datum[2]}"
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

    Kontakt: { md['user_kontakt'] }
    Ihr Link für neue Meldungen:
    https://gottesanbeterin-gesucht.de/report/{ md['id'] }
    
    {'Latitude:':<21}  {md['latitude']:>22}
    {'Longitude:':<21}  {md['longitude']:>22}
    {'PLZ:':<21}  {str(md['plz']):>22}
    {'Ort:':<21}  {md['ort']:>22}
    {'Straße:':<21}  {md['strasse']:>22}
    {'Bundesland:':<21} {md['land']:>22}
    {'Kreis:':<21} {md['kreis']:>22}
    {'Funddatum:':<21} {md['formdat']:>22}

    ==========

    Folgendes Geschlecht bzw. Entwicklungsstadium wurden festgestellt:

    (siehe auch:  https://gottesanbeterin-gesucht.de/bestimmung)
    
    {'Männchen:':<10} {str(md['art_m']) + " ":10}
    {'Weibchen:':<10} {str(md['art_w']) + " ":<10}
    {'Nymphe(n):':<10} {str(md['art_n']) + " ":<10}
    {'Oothek(n):':<10} {str(md['art_o']) + " ":<10}
    {md['anm_bearbeiter']}

    WICHTIGER HINWEIS:

    - Behandeln Sie den Link wie ein Passwort!
    - Publizieren Sie den Link nicht in Foren, Messengern, ...
    """.format(md)


def renderhtmlmsg(data):
    md = data.json

    if md['anm_bearbeiter'] == '':
        text = 'Keine Anmerkung(en) vom Reviewer.'
    else:
        text = 'Anmerkung(en) vom Reviewer: ' + md['anm_bearbeiter']
    md['anm_bearbeiter'] = text
    datum = md['dat_fund_von'].split(' ')[1:4]
    md['formdat'] = f"{datum[0]}. {datum[1]}. {datum[2]}"
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
    <td>Kontakt:</td><td>{ md['user_kontakt'] }</td>
    </tr>
    <tr>    
    <td>Ihr Link für weitere Meldungen</td>
    <td>https://gottesanbeterin-gesucht.de/report/{ md['id'] }</td>
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
    <td>{md['formdat']}</td>
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
     <td>WICHTIGER HINWEIS:</td>
    </tr>    
    <tr>
     <td>
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
    text = rendertextmsg(data)
    html = renderhtmlmsg(data)

    subject = "Meldebestätigung"
    smtp_server = Config.host
    login = Config.sender_email  # paste your login generated by Mailtrap
    password = Config.sender_pass  # paste your password generated by Mailtrap

    sender_email = Config.sender_email
    receiver_email = formdata.contact.data
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = receiver_email

    text = rendertextmsg(formdata)
    html = renderhtmlmsg(formdata)

    # convert both parts to MIMEText objects and add them to the MIMEMultipart message
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(Config.host, Config.port) as server:
            server.starttls(context=context)
            server.login(Config.sender_email, Config.sender_pass)
            server.sendmail(Config.sender_email,
                            receiver_email, message.as_string())
    except Exception as ex:
        raise ex
