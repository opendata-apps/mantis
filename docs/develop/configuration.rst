Konfiguration
=============

Konfigurationsquellen
---------------------

Die Laufzeitkonfiguration wird in ``app/config.py`` aufgebaut.

Reihenfolge:

1. ``.env`` wird per ``load_dotenv()`` geladen.
2. Werte werden aus Umgebungsvariablen gelesen.
3. Nicht gesetzte Werte fallen auf Defaults aus ``Config`` zurück.
4. Container-Deployments überschreiben einzelne Werte über Compose-Environment.

Wichtige Regeln
---------------

- ``SECRET_KEY`` ist in Produktion verpflichtend.
- ``UPLOAD_FOLDER`` muss ein absoluter Pfad sein, falls gesetzt.
- ``BACKUP_DIR`` muss ein absoluter Pfad sein, falls gesetzt.
- Datenbank-URI wird aus ``POSTGRES_*`` und ``DATABASE_*`` zusammengesetzt.

Umgebungsvariablen
------------------

Kern
^^^^

.. list-table::
   :header-rows: 1

   * - Variable
     - Default
     - Bedeutung
   * - ``FLASK_ENV``
     - ``development``
     - Laufzeitmodus (steuert u. a. SECRET_KEY-Validierung in Produktion)
   * - ``FLASK_DEBUG``
     - ``1`` (lokal)
     - Flask Debug-Modus
   * - ``SECRET_KEY``
     - kein fixer Default
     - Signatur von Session/CSRF-Token

Datenbank
^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Variable
     - Default
     - Bedeutung
   * - ``POSTGRES_DB``
     - ``mantis_tracker``
     - Datenbankname
   * - ``POSTGRES_USER``
     - ``mantis_user``
     - Datenbankbenutzer
   * - ``POSTGRES_PASSWORD``
     - ``mantis``
     - Datenbankpasswort
   * - ``DATABASE_HOST``
     - ``localhost``
     - Datenbankhost (Container: ``db``)
   * - ``DATABASE_PORT``
     - ``5432``
     - Datenbankport

Connection-Pool
^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Variable
     - Default
     - Bedeutung
   * - ``DB_POOL_SIZE``
     - ``10``
     - Basispoolgröße
   * - ``DB_MAX_OVERFLOW``
     - ``20``
     - Zusätzliche Verbindungen über Poolgröße hinaus
   * - ``DB_POOL_RECYCLE``
     - ``3600``
     - Recycle-Zeit in Sekunden

Dateiablage
^^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Variable
     - Default
     - Bedeutung
   * - ``UPLOAD_FOLDER``
     - ``app/datastore`` (absolut aufgelöst)
     - Basisordner für Uploads
   * - ``BACKUP_DIR``
     - ``backups`` (absolut aufgelöst)
     - Zielordner für erzeugte Backup-ZIP-Dateien

Mail
^^^^

.. list-table::
   :header-rows: 1

   * - Variable
     - Default
     - Bedeutung
   * - ``MAIL_SERVER``
     - ``mail.mantis-projekt.de``
     - SMTP-Server
   * - ``MAIL_PORT``
     - ``25``
     - SMTP-Port
   * - ``MAIL_USE_TLS``
     - ``True``
     - TLS aktiv
   * - ``MAIL_USE_SSL``
     - ``False``
     - SSL aktiv
   * - ``MAIL_USERNAME``
     - leer
     - SMTP-Benutzer
   * - ``MAIL_PASSWORD``
     - leer
     - SMTP-Passwort
   * - ``MAIL_DEFAULT_SENDER``
     - ``mantis@projekt.de``
     - Standard-Absenderadresse
   * - ``MAIL_DEFAULT_SENDER_NAME``
     - ``Mantis-Projekt``
     - Standard-Absendername
   * - ``REVIEWERMAIL``
     - ``False``
     - Aktiviert Reviewer-Mailversand
   * - ``BACKUPMAIL``
     - leer
     - Empfängeradresse für Backup-Downloadlinks

Security/Session
^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Variable
     - Default
     - Bedeutung
   * - ``PREFERRED_URL_SCHEME``
     - ``https`` (Config) / ``http`` (.env.example)
     - URL-Schema; beeinflusst u. a. HSTS-Header
   * - ``SESSION_COOKIE_SECURE``
     - ``True`` (Config) / ``False`` (.env.example)
     - Secure-Flag für Session-Cookie
   * - ``BACKUP_DOWNLOAD_MAX_AGE_SECONDS``
     - ``604800``
     - Gültigkeitsdauer signierter Backup-Downloadlinks

Sonstiges
^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Variable
     - Default
     - Bedeutung
   * - ``FLASK_LOG_LEVEL``
     - ``INFO``
     - Loglevel für Datei-Logging außerhalb Debug-Modus
   * - ``CELEBRATION_THRESHOLD``
     - ``10000``
     - Schwelle für UI-Feierzustand auf der Startseite
   * - ``WEB_PORT``
     - ``5000``
     - Externer Port im Containerbetrieb
   * - ``PROJECT_NAME``
     - ``mantis``
     - Compose-Projektname

Praxisprofile
-------------

Lokale Entwicklung
^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   FLASK_ENV=development
   FLASK_DEBUG=1
   PREFERRED_URL_SCHEME=http
   SESSION_COOKIE_SECURE=False

Produktion
^^^^^^^^^^

.. code-block:: bash

   FLASK_ENV=production
   FLASK_DEBUG=0
   SECRET_KEY=<generated>
   PREFERRED_URL_SCHEME=https
   SESSION_COOKIE_SECURE=True
