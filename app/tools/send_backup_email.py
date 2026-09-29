from flask import current_app
from flask_mail import Message

from app.extensions import mail


def render_backup_email(download_url: str) -> str:
    """Build the reviewer backup notification email body."""
    return f"""
    Lieber Reviewer,

    soeben wurde eine Datensicherung durchgeführt.

    Die Zip-Datei mit den Bildern des Jahres und dem Datenbank-Dump
    kann mit folgendem Link gespeichert werden:

    {download_url}

    Zum Herunterladen benötigen Sie eine aktive Reviewer-Sitzung.
    Öffnen Sie zuerst Ihren persönlichen Reviewer-Link im selben Browser.

    Mit freundlichen Grüßen

    Ihr Team vom Mantis-Portal
    """


def send_backup_email(
    *,
    recipient: str,
    download_url: str,
) -> None:
    msg = Message(
        subject="[Gottesanbeterin-Gesucht] Backup",
        recipients=[recipient],
        body=render_backup_email(download_url),
    )
    mail.send(msg)
    current_app.logger.info("Backup mail sent to %s.", recipient)
