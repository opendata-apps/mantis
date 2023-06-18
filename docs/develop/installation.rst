🦗 Mantis Tracker 🦗
=====================


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

💻 Setup/Installation
---------------------
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
Der Einsatz von Tailwind für das CSS, erfordet den Einsatz von Node.js.
Die Abhängigkeiten sind in der Datei ``package.json`` festgehalten.

::

    # Einmalig   
    npm install
    # oder hinter einem Proxy
    npm --proxy <your-proxy> install

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

Liste der verwendeten Pakete
----------------------------

.. index:: Installationspakete
	   
Die Liste wurde erzeug mit: ``pip freeze``
::
         
   alabaster==0.7.13
   alembic==1.10.2
   Babel==2.12.1
   blinker==1.6.2
   certifi==2023.5.7
   charset-normalizer==3.1.0
   click==8.1.3
   colorama==0.4.6
   docutils==0.19
   Flask==2.2.3
   Flask-Migrate==4.0.4
   Flask-SQLAlchemy==3.0.3
   Flask-WTF==1.1.1
   greenlet==2.0.2
   idna==3.4
   imagesize==1.4.1
   itsdangerous==2.1.2
   Jinja2==3.1.2
   Mako==1.2.4
   MarkupSafe==2.1.2
   packaging==23.1
   psycopg2-binary==2.9.6
   Pygments==2.15.1
   python-dotenv==1.0.0
   requests==2.30.0
   snowballstemmer==2.2.0
   SQLAlchemy==2.0.7
   typing_extensions==4.5.0
   urllib3==2.0.2
   waitress==2.1.2
   Werkzeug==2.2.3
   WTForms==3.0.1
