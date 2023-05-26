from send_email import *

anzahl = 423
anzahl1 = "123"
anzahl2 = "4565637467"
anzahl3 = "789"
plz = "14480"

# hier kommt eine Fallunterscheidung durch eine Datenbankabfrage rein
anzahl_andere = None

antwort_bestaetigung_oothek = f"""
Liebe/r Mantis-Freund*In,
wir möchten Ihnen mitteilen, dass wir Ihre Meldung überprüft haben. Sie
haben ein Eigelege (Oothek) der Europäischen Gottesanbeterin (Mantis
religiosa) gefunden. Die Weibchen legen ab etwa September ihre Ootheken.
Die Ootheken überdauern die kalte Jahreszeit ohne jeglichen Schutz,
wohingegen die erwachsenen Tiere den Winter nicht überstehen. Das ist
aber ganz normal. Im Mai/Juni des Folgejahres schlüpft dann die neue
Gottesanbeterinnengeneration. Falls Sie im kommenden Jahr die
Beobachtung machen, dass Jungtiere schlüpfen, würden wir uns freuen, wenn
Sie uns dies mitteilen würden. Ein Foto und eine Meldung sind
schnellgemacht. Ootheken sind der Nachweis von Reproduktion und somit
ganz wertvolle Meldungen für dieBeurteilung von Funden an einem Ort.

Mit Ihrem Fund liegen uns seit Projektbeginn 2017 nun {anzahl1}
bestätigte Fundmeldungen aus Brandenburg und Berlin vor. Allein in
diesem Jahr waren es bereits {anzahl2} bestätigte Mitteilungen. Aus dem
Postleitzahlgebiet {plz} wurde die Art bisher {anzahl3} Mal nachgewiesen
und uns mitgeteilt. Somit möchten wir uns noch einmal recht
herzlich für Ihre Fundmeldung bedanken. Mit jeder Meldung wird das
Bild über die Verbreitung und Ausbreitung der Art klarer. Falls
Sie der Gottesanbeterin erneut begegnen, würden wir uns sehr
freuen, wieder von Ihnen zu hören.

Mit freundlichen Grüßen

Ihr Team vom Mantis-Portal
"""

if __name__ == "__main__":
    subject = "Hallo"
    content = antwort_bestaetigung_oothek.format(
        anzahl1, anzahl2, plz, anzahl3
    )
    to = "Mantis-Melder@irgendwo.de"
    send_email(subject, content, to)
