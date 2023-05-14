# 🦗 Mantis Tracker 🦗

![Header Banner](https://i.ibb.co/fxgcjgC/image-2023-05-02-210757973.png)

Eine interaktive Webanwendung zur Erfassung von Mantis Religiosa-Sichtungen in Brandenburg, präsentiert vom Naturkunde Museum Potsdam.

Mantis Tracker ermöglicht es Benutzern, Mantis Religiosa-Sichtungen zu melden und sie auf einer interaktiven Karte anzuzeigen, zusammen mit aufschlussreichen Statistiken und hilfreichen FAQs.

## 🌟 Funktionen

- 📚 Erfahren Sie mehr über die Mantis Religiosa
- 🎨 Schöne Benutzeroberfläche
- 📝 Melden Sie Mantis-Sichtungen mit einem einfach zu bedienenden Formular
- 🗺️ Alle Mantis-Sichtungen auf einer interaktiven Karte anzeigen
- 📊 Aufschlussreiche Statistiken und FAQs einsehen

## 🛠️ Technologien

![HTML](https://img.shields.io/badge/-HTML-000000?style=flat&logo=HTML5)
![CSS](https://img.shields.io/badge/-CSS-000000?style=flat&logo=CSS3&logoColor=1572B6)
![Jinja2](https://img.shields.io/badge/-Jinja2-000000?style=flat&logo=jinja)
![Python](https://img.shields.io/badge/-Python-000000?style=flat&logo=python)
![Flask](https://img.shields.io/badge/-Flask-000000?style=flat&logo=flask)
![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-000000?style=flat&logo=postgresql)
![Tailwind CSS](https://img.shields.io/badge/-Tailwind%20CSS-000000?style=flat&logo=tailwind-css)
![JavaScript](https://img.shields.io/badge/-JavaScript-000000?style=flat&logo=javascript)

## 💻 Entwicklungseinrichtung/Installation

```bash
# Repository klonen
git clone https://gitlab.com/opendata-apps/mantis.git
cd mantis_flask

# Virtuelle Umgebung erstellen und aktivieren
python -m venv venv
source venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# PostgreSQL-Datenbank erstellen
sudo -u postgres psql
CREATE DATABASE mantis_tracker;
CREATE USER mantis_user WITH PASSWORD 'mantis';
GRANT ALL PRIVILEGES ON DATABASE mantis_tracker TO mantis_user;
\q

# Wenn sich die Datenbankstruktur geändert hat
flask db migrate -m "Ihr Kommentar"

# Datenbanktabellen erstellen
flask db upgrade

# CSS-Beobachter ausführen
npx tailwindcss -i app/static/css/theme.css -o app/static/build/theme.css --watch

# Entwicklungsserver starten
python run.py oder
flask run (mit --debug für Debug-Modus mit Neuladen)

# Öffnen Sie http://localhost:5000 in Ihrem Browser
```

## 📝 Lizenz

Dieses Projekt ist unter der [MIT](https://choosealicense.com/licenses/mit/) Lizenz lizenziert.