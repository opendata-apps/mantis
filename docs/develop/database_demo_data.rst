=========================
 Neuanlage der Demodaten
=========================
Für die Neuentwicklung sind Demodaten im Testordner vorbereitet.

Eine Neuanlage erfolgt mit folgenden Schritten:

1. In der Datenbank

   ::

      \c postgres
      drop database mantis_tracker;
      create database mantis_tracker;

2. In der virutellen Umgebung (venv)

   ::

      rm -rf migrations
      flask db init
      flask db migrate -m "Initialisierung"
      rm -rf migrations/

3. Einlesen der Demodaten

   Siehe ``manits/tests/demaodata/demo-data-main.sql``
