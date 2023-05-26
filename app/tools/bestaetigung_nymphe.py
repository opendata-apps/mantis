from send_email import *

anzahl = 423
anzahl1 = "123"
anzahl2 = "4565637467"
anzahl3 = "789"
plz = "14480"

# hier kommt eine Fallunterscheidung durch eine Datenbankabfrage rein
anzahl_andere = None

antwort_bestaetigung_nymphe = f"""
Liebe/r Mantis-Freund*In,
wir möchten Ihnen mitteilen, dass wir Ihre Meldung überprüft
haben. Bei dem Tier auf Ihrem Bild handelt es sich um eine
junge Europäische Gottesanbeterin (Mantis religiosa), eine
sogenannte Nymphe oder Larve. Das kann man an den noch
fehlenden Flügeln gut erkennen. Die Flügel erscheinen erst
beim Vollinsekt, also nach der letzten Häutung. Danach sind
die Tiere erwachsen und häuten sich nicht mehr. Ab Ende Juli
werden die Tiere für gewöhnlich erwachsen. Manchmal treten
Nymphen noch bis in den September hinein auf.

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
    content = antwort_bestaetigung_nymphe.format(
        anzahl1, anzahl2, plz, anzahl3
    )
    to = "Mantis-Melder@irgendwo.de"
    send_email(subject, content, to)
