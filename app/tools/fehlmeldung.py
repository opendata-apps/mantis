from send_email import *


geschlecht = "Weibchen"
art1 = "Warzenbeißer"
art2 = "Heuschrecken"

# hier kommt eine Fallunterscheidung durch eine Datenbankabfrage rein
anzahl_andere = None

antwort_fehlmeldung = f"""
Liebe/r Mantis-Freund*In,

mit Ihrer Fundmeldung haben Sie sich an unserem
Gottesanbeterinnen-Monitoring beteiligt. Dafür danken
wir Ihnen sehr. Die Prüfung Ihres Belegfotos hat aber
ergeben, dass Sie leider keine Gottesanbeterin
gefunden haben. Auf Ihrem Foto haben wir ein
{geschlecht} des {art1} gesehen.

Dennoch ist auch dieser Fund für die Kenntnis der
Biodiversität Brandenburgs und Berlin wichtig.
Sie brauchen nichts weiter zu tun. Wir würden ihren
Nachweis in unsere {art2}-Datenbank einfügen.
Kein Datensatz geht verloren. Also noch einmal vielen
Dank für Ihre Meldung.

Mit freundlichen Grüßen

Ihr Team vom Mantis-Portal
"""

if __name__ == "__main__":
    subject = "Hallo"
    content = antwort_fehlmeldung.format(geschlecht, art1, art2)
    to = "Mantis-Melder@irgendwo.de"
    send_email(subject, content, to)
