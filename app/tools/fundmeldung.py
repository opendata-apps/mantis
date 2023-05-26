from send_email import *

anzahl = 423


# hier kommt eine Fallunterscheidung durch eine Datenbankabfrage rein
anzahl_andere = None

antwort_bestaetigung = f"""
Liebe/r Mantis-Freund*In,

Vielen Dank, dass Sie sich am Gottesanbeterinnen-Monitoring beteiligt
haben. Ihre Meldung ist bei uns eingegangen. Seit Projektbeginn
wurden uns {anzahl} Meldungen aus Brandenburg und Berlin zugesendet.
Vor allem aus dem Süden unseres Bundeslandes. Im Norden wird die Art
viel seltener gesichtet. Aus Berlin erhielten wir in den vergangenen
Jahren vermehrt Meldungen quer über das Stadtgebiet verteilt. Um die
Situation darstellen zu können, zählt für uns nach wie vor jede
Meldung. Sobald wir Ihren Fund überprüft und freigegeben haben, wird
er in der Verbreitungskarte angezeigt. Im Weiteren erhalten Sie dann
noch die Information, ob es sich um eine Gottesanbeterin gehandelt
hat oder um eine andere Art. Sollte Ihre Fundmeldung nicht aus
Brandenburg und Berlin sein, geht sie aber auch nicht verloren.
Wir nehmen Sie mit in unsere Datenbank auf und stehen im Kontakt
mit Kolleg*Innen in anderen Bundesländern. In jedem Fall noch einmal
vielen Dank für Ihre Meldung. Sobald das Geschlecht des gemeldeten
Tieres ermittelt ist, erhalten Sie von uns eine weitere Email.

Mit freundlichen Grüßen

Ihr Team vom Mantis-Portal
"""

if __name__ == "__main__":
    subject = "Hallo"
    content = antwort_bestaetigung.format(anzahl)
    to = "Mantis-Melder@irgendwo.de"
    send_email(subject, content, to)
