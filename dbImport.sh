#!/bin/bash

# navigate to your project directory
cd /home/leon/Documents/GitHub/mantis

# Postgres credentials
export PGPASSWORD='postgres'
database='mantis_tracker'
user='postgres'

# Drop and recreate the database
psql -U $user -c "DROP DATABASE IF EXISTS $database(force);"
psql -U $user -c "CREATE DATABASE $database;"

# Flask migrations
rm -rf migrations
flask db init
flask db migrate -m "Initialisierung aller Relationen"
flask db upgrade

# Insert data from SQL files
psql -U $user -d $database -f tests/demodata/beschreibung.sql
psql -U $user -d $database -f app/datastore/test.sql

# Update sequence values
psql -U $user -d $database -c "SELECT setval('beschreibung_id_seq', (SELECT MAX(id) FROM beschreibung));"
psql -U $user -d $database -c "SELECT setval('fundorte_id_seq', (SELECT MAX(id) FROM fundorte));"
psql -U $user -d $database -c "SELECT setval('meldungen_id_seq', (SELECT MAX(id) FROM meldungen));"
psql -U $user -d $database -c "SELECT setval('melduser_id_seq', (SELECT MAX(id) FROM melduser));"
psql -U $user -d $database -c "SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));"
