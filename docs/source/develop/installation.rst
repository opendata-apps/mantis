🦗 Mantis Tracker 🦗
---------------------


🛠️ Technologien
-----------------
.. image:: https://img.shields.io/badge/-HTML-000000?style=flat&logo=HTML5
.. image:: https://img.shields.io/badge/-CSS-000000?style=flat&logo=CSS3&logoColor=1572B6
.. image:: https://img.shields.io/badge/-Jinja2-000000?style=flat&logo=jinja
.. image:: https://img.shields.io/badge/-Python-000000?style=flat&logo=python
.. image:: https://img.shields.io/badge/-Flask-000000?style=flat&logo=flask
.. image:: https://img.shields.io/badge/-PostgreSQL-000000?style=flat&logo=postgresql
.. image:: https://img.shields.io/badge/-Tailwind%20CSS-000000?style=flat&logo=tailwind-css
.. image:: https://img.shields.io/badge/-JavaScript-000000?style=flat&logo=javascript

💻 Entwicklungs-Setup/Installation
------------------------------------
Schritt 1: 📁 Klonen Sie das Repository

::

   git clone https://gitlab.com/opendata-apps/mantis.git
   cd mantis

.. index:: venv
.. index:: virtualenviroment

Schritt 2: 🌐 Erstellen Sie eine virtuelle Umgebung und aktivieren Sie sie

::
    
   python -m venv .venv (or another name with . like .mantis)
   source .venv/bin/activate    # For Windows: .venv\Scripts\activate  

Schritt 3: 📦 Installieren Sie die Abhängigkeiten

::

   pip install -r requirements.txt

.. index:: Datenbank

Schritt 4: 🗄️ Erstellen Sie eine PostgreSQL-Datenbank

::

   psql -U postgres

::

   CREATE DATABASE mantis_tracker;
   CREATE USER mantis_user WITH PASSWORD 'mantis';
   GRANT ALL PRIVILEGES ON DATABASE mantis_tracker TO mantis_user;
   \q


Schritt 5: 📝 Initilisieren der Almebic-Versionsverwaltung

Es wird der Ordner »``Migration``« angelegt.

::

   flask db init

Schritt 6: 🔄 Nur wenn sich die Datenbankstruktur geändert hat.

::

   flask db migrate -m "your comment"
   
.. index:: Migration Datenbank
	   
Schritt 7: 🏗️ Erstellen Sie die Datenbanktabellen

::

   flask db upgrade

Schritt 8: 📈 Importieren Sie die Daten

::

   \copy plzort(plz, ort, bundesland, landkreis) FROM 'C:\home\mantis\app\database\ww-german-postal-codes.csv' WITH (FORMAT csv, DELIMITER ',', HEADER true, ENCODING 'utf-8')

.. index:: CSS-Watcher; Tailwind
.. index:: Tailwind; CSS-Watcher	   
	   
Schritt 9: 🎨 Starten Sie den CSS-Watcher

::

    npm --proxy <your-proxy> install tailwindcss

::

    npx tailwindcss -i app/static/css/theme.css -o app/static/build/theme.css --watch

Schritt 10: 🚀 Starten Sie den Entwicklungsserver

::

    python run.py

Schritt 11: 🏢 Starten Sie den Produktions-Server

::

    # For Linux
    gunicorn run:app    

    # For Windows
    waitress-serve run:app

Schritt 12: 🌐 Öffnen Sie http://localhost:5000 in Ihrem Browser.

