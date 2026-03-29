import logging

from flask import current_app
from flask_mail import Message
from datetime import datetime, timedelta
from app import mail


logger = logging.getLogger(__name__)


def rendertextmsg(md):
 
    datum = datetime.now() + timedelta(days=7)
    return f"""
    Lieber Reviewer,

    soeben wurde eine Datensicherung durchgeführt.

    Die Zip-Datei mit den Bildern des Jahres und
    dem Dump der Datenbank, kann mit folgendem Link
    gespeichert werden:

    https://gottesanbeterin-gesucht.de/save/{md["backup"]}

    Güliger Link bis zum {datum.strftime('%d.%m.%Y')}.


    Mit freundlichen Grüßen

    Ihr Team vom Mantis-Portal
    
    """


def send_backup_email(data):
    md = data
    msg = Message(
        subject="[Gottesanbeterin-Gesucht] Backup",
        recipients=[data["user_kontakt"]],
        sender=data["sender"],
        body=(rendertextmsg(md)),
    )

    current_app.logger.info(f"Mail an {data['user_kontakt']} verschickt.")


if __name__ == "__main__":
    import datetime

    from app import create_app

    data = {
        "user_id": "xxxxxxxxx",
        "user_kontakt": "test@example.com",
        "backup": "backup_2025.zip",
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
