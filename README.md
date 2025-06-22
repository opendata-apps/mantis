# 🦗 [Gottesanbeterin Gesucht Mitmachprojekt](https://gottesanbeterin-gesucht.de/) 🦗

![Header Banner](https://i.ibb.co/QrjJ7NM/berger03.webp)

An interactive web application to track Mantis Religiosa sightings in Brandenburg, presented by the Naturkundemuseum Potsdam.

Mantis Tracker allows users to report Mantis Religiosa sightings and view them on an interactive map, along with insightful statistics and helpful FAQs.

## 🌟 Features

- 📚 Learn about the Mantis Religiosa
- 🎨 Beautiful UI
- 📝 Report mantis sightings with an easy-to-use form
- 🗺️ View all mantis sightings on an interactive map
- 📊 View insightful statistics and FAQs

## 🚀 Roadmap

Here are some of the features we plan to add in the future:

- [ ] Gallery of photos of the Mantis Religiosa
- [ ] Improved data visualization and analysis of the sighting data
- [ ] More animations and UI improvements to make the app more engaging
- [ ] Improved performance and code quality

Stay tuned for updates on these exciting new features!

## 🛠️ Technologies

![HTML](https://img.shields.io/badge/-HTML-000000?style=flat&logo=HTML5)
![CSS](https://img.shields.io/badge/-CSS-000000?style=flat&logo=CSS3&logoColor=1572B6)
![Jinja2](https://img.shields.io/badge/-Jinja2-000000?style=flat&logo=jinja)s
![Python](https://img.shields.io/badge/-Python-000000?style=flat&logo=python)
![Flask](https://img.shields.io/badge/-Flask-000000?style=flat&logo=flask)
![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-000000?style=flat&logo=postgresql)
![Tailwind CSS](https://img.shields.io/badge/-Tailwind%20CSS-000000?style=flat&logo=tailwind-css)
![JavaScript](https://img.shields.io/badge/-JavaScript-000000?style=flat&logo=javascript)

# 💻 Development Setup

### Prerequisites

- Python 3.8+
- Node.js and npm
- PostgreSQL

### Step 1: 📁 Clone the repository

```bash
git clone https://gitlab.com/opendata-apps/mantis.git
cd mantis
```

### Step 2: 🌐 Create and activate virtual environment

```bash
python -m venv .venv
source .venv/bin/activate    # For Windows: .venv\Scripts\activate
```

### Step 3: 📦 Install Python dependencies

```bash
pip install -r requirements.txt
```

### Step 4: 🗄️ Set up PostgreSQL database

Using `psql`:

```bash
psql -U postgres
```

Preapare a database for production.

```sql
CREATE USER mantis_user WITH PASSWORD 'mantis';
CREATE DATABASE mantis_tracker OWNER mantis_user;
GRANT ALL PRIVILEGES ON DATABASE mantis_tracker TO mantis_user;
-- MacOS only:
GRANT usage, create ON SCHEMA public TO mantis_tracker;
\q
```

Prepare a database for pytest

```sql
CREATE DATABASE mantis_tester OWNER mantis_user;
GRANT ALL PRIVILEGES ON DATABASE mantis_tester TO mantis_user;
-- MacOS only:
GRANT usage, create ON SCHEMA public TO mantis_tester;
\q
```

### Step 5: 🏗️ Create the database tables

```bash

flask db upgrade

# aktuelle Version anzeigen
flask db current

# History anzeigen

flask db history

```

### Step 6: ☕ Fill the database tables

If TESTING in config.py is set to TRUE also
Demodata are inserted into the database.

```bash
flask insert-initial-data
```

### Step 7: 🎨 Run the CSS watcher

```bash
cd app/static
npm install
```

The project includes a convenient script to watch for CSS changes. Start it with:

```bash
npm run watch:css
```

### Step 8: 🚀 Run the application

#### Development server

```bash
python run.py
```

### Step 9: 🚀 Connect as Reviewer

```bash
http://loclahost:5000/reviewer/9999
```

# Start with fresh databases

- delete database mantis_tracker
- delete database mantis_tester
- start again with Step 4

# Production setup

- Edit Settings in app/config.py and make changes e.g.
  - Connectionstring for DB
  - TESTING = False
  - Run Tests with pytest
- Create the minified CSS file

```bash
cd app/static
npm run build:css
```

### Step 9: 🏢 Run production server

```bash
gunicorn run:app    # For Windows: waitress-serve --listen=*:8000 run:app
```

### Step 8: 🌐 Access the application

Open [http://localhost:5000](http://localhost:5000) in your browser.
