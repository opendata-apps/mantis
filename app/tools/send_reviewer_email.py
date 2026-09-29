import logging

from email_validator import validate_email
from flask_mail import Message

from app.extensions import mail

logger = logging.getLogger(__name__)


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
    Kontakt: {md["user_kontakt"]}

    {"Latitude:":<21}  {md["latitude"]:>22}
    {"Longitude:":<21}  {md["longitude"]:>22}
    {"PLZ:":<21}  {md["plz"] or "":>22}
    {"Ort:":<21}  {md["ort"]:>22}
    {"Straße:":<21}  {md["strasse"]:>22}
    {"Bundesland:":<22} {md["land"]:>22}
    {"Kreis:":<22} {md["kreis"]:>22}
    {"Funddatum:":<22} {md["datum"]:>22}

    ==========

    Folgendes Geschlecht bzw. Entwicklungsstadium wurden festgestellt:

    Siehe auch:
    https://gottesanbeterin-gesucht.de/bestimmung

    {"Männchen:":<10} {str(md["art_m"]) + " ":10}
    {"Weibchen:":<10} {str(md["art_w"]) + " ":<10}
    {"Nymphe(n):":<10} {str(md["art_n"]) + " ":<10}
    {"Oothek(n):":<10} {str(md["art_o"]) + " ":<10}
    {md["anm_bearbeiter"]}

    Ihr Link für neue Meldungen:
    https://gottesanbeterin-gesucht.de/melden/{md["user_id"]}

    WICHTIGER HINWEIS:

    - Behandeln Sie den Link wie ein Passwort!
    - Publizieren Sie den Link nicht in Foren, Messengern, ...
    """


def build_email_payload(meldung) -> dict:
    """Collect what ``rendertextmsg`` needs from a loaded report.

    Each value is read from the table it belongs to. The caller must pass a
    report whose ``fundort`` and ``reporter_link`` relationships are loaded.
    """
    fundort = meldung.fundort
    reporter = meldung.reporter_link.reporter
    return {
        "user_id": reporter.user_id,
        "user_kontakt": reporter.user_kontakt,
        "anm_bearbeiter": meldung.anm_bearbeiter,
        "dat_fund_von": meldung.dat_fund_von,
        "latitude": fundort.latitude,
        "longitude": fundort.longitude,
        "plz": fundort.plz,
        "ort": fundort.ort,
        "strasse": fundort.strasse,
        "land": fundort.land,
        "kreis": fundort.kreis,
        "art_m": meldung.art_m,
        "art_w": meldung.art_w,
        "art_n": meldung.art_n,
        "art_o": meldung.art_o,
    }


def send_email(data):
    md = dict(data)
    if not md["anm_bearbeiter"]:
        text = "Keine Anmerkung(en) vom Reviewer."
    else:
        text = f"Anmerkung(en) vom Reviewer: {md['anm_bearbeiter']}"
    md["anm_bearbeiter"] = text
    string_from_date = md["dat_fund_von"].strftime("%d.%m.%Y")
    md["datum"] = string_from_date

    # Flask-Mail submits through smtplib.sendmail, which puts the envelope on
    # the wire as ASCII and has no SMTPUTF8 path. An internationalised domain
    # therefore has to be converted to punycode here, immediately before
    # submission — the database keeps the address in the form the reporter
    # knows. allow_smtputf8=False makes an umlaut before the @ raise here rather
    # than yield ascii_email=None, which Message takes and fails on much later.
    validated = validate_email(
        data["user_kontakt"], check_deliverability=False, allow_smtputf8=False
    )
    # None only for addresses needing SMTPUTF8, which the call above rejects.
    assert validated.ascii_email is not None
    recipient = validated.ascii_email

    msg = Message(
        subject="[Gottesanbeterin-Gesucht] Meldung überprüft",
        recipients=[recipient],
        body=(rendertextmsg(md)),
    )

    mail.send(msg)
    logger.info("Mail an %s verschickt.", data["user_kontakt"])
