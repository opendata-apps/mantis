from send_email import *

geschlecht = "Weibchen"
anzahl1 = "123"
anzahl2 = "4565637467"
anzahl3 = "789"
plz = "14480"

antwort_bestaetigung_weibl = f"""

Liebe/r Mantis-Freund*In,
wir möchten Ihnen mitteilen, dass wir Ihre Meldung überprüft haben.
Bei dem Tier auf Ihrem Bild handelt es sich um ein erwachsenes
{geschlecht} der Europäischen Gottesanbeterin (Mantis religiosa).
Die Weibchen sind korpulenter und größer (dicker als ein Bleistift)
als die Männchen (dünner als ein Bleistift), was man natürlich nur
im direkten Vergleich sieht, wenn man die Tiere nicht kennt. Man
kann die Geschlechter aber auch ganz gut an den Fühlern
unterscheiden. Die Weibchen haben dünn-fadenförmige Antennen, die
kürzer sind als die Vorderbrust des Tieres. Bei den Männchen
hingegen sind die Antennen an der Basis (also am Kopf) etwas
verdickt und laufen zur Spitze hin spitz zu. Das kann man auf
Ihrem Bild gut erkennen.

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
    content = antwort_bestaetigung_weibl.format(
        geschlecht, anzahl1, anzahl2, plz, anzahl3
    )
    to = "Mantis-Melder@irgendwo.de"
    send_email(subject, content, to)
