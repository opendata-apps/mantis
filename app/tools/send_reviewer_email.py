from flask_mail import Message
from app import create_app, mail
import datetime


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
    {'Bundesland:':<22} {md['land']:>22}
    {'Kreis:':<22} {md['kreis']:>22}
    {'Funddatum:':<22} {md['datum']:>22}

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


def send_email(data):
    md = data
    if not md['anm_bearbeiter']:
        text = "Keine Anmerkung(en) vom Reviewer."
    else:
        text = f"Anmerkung(en) vom Reviewer: {md['anm_bearbeiter']}"
    md['anm_bearbeiter'] = text
    string_from_date = md['dat_fund_von'].strftime('%d.%m.%Y')
    md['datum'] = string_from_date

    msg = Message(
        subject="[Gottesanbeterin-Gesucht] Meldung überprüft",
        recipients=[data["user_kontakt"]],
        body=(rendertextmsg(md))
    )

    app = create_app()
    with app.app_context():
        mail.send(msg)
        print(f"✅ Mail an {data['user_kontakt']} verschickt.")


if __name__ == "__main__":
    # check script with real data and:
    # cd project-root
    # python -m app.tools.send_reviewer_email

    data = {
        "user_id": "xxxxxxxxx",
        "user_kontakt": "test@example.com",
        "anm_bearbeiter": "",
        "datum": datetime.datetime.today(),
        "dat_fund_von": datetime.datetime.today(),
        "latitude": "3.14",
        "longitude": "6.28",
        "plz": "123456",
        "ort": "Nirgendwo",
        "strasse": "Irgendwo",
        "land": "Lummerland",
        "kreis": "bahn",
        "art_m": 0,
        "art_w": 1,
        "art_n": 2,
        "art_o": 3,
    }
    app = create_app()
    with app.app_context():
        try:
            send_email(data)
        except OSError as err:
            print("OS error:", err)
        except ValueError:
            print("Could not convert data to an integer.")
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            raise
