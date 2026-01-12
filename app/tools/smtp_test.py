import smtplib
from email.mime.text import MIMEText

SMTP_SERVER = ""  # oder Provider
SMTP_PORT = 587  # 587 = TLS, 465 = SSL
SMTP_USER = ""
SMTP_PASS = ""
FROM_ADDR = ""
TO_ADDR = ""

msg = MIMEText("Hallo,\n\nDies ist ein SMTP-Test.\n\nGruß")
msg["Subject"] = "SMTP Test"
msg["From"] = FROM_ADDR
msg["To"] = TO_ADDR

try:
    print(f"🔌 Verbinde zu {SMTP_SERVER}:{SMTP_PORT} ...")
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
    server.ehlo()

    # Falls TLS genutzt wird
    if SMTP_PORT == 587:
        print("🔒 Starte TLS ...")
        server.starttls()
        server.ehlo()

        print("🔑 Logge ein ...")
        server.login(SMTP_USER, SMTP_PASS)

        print(f"📨 Sende Mail an {TO_ADDR} ...")
        server.sendmail(FROM_ADDR, [TO_ADDR], msg.as_string())

        print("✅ Mail erfolgreich verschickt!")
        server.quit()

except Exception as e:
    print("❌ Fehler:", e)
