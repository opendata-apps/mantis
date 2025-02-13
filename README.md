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

# 💻 Development Setup/Installation

### Step 1: 📁 Clone the repository

```bash
git clone https://gitlab.com/opendata-apps/mantis.git
cd mantis
```

### Step 2: 🌐 Create a virtual environment and activate it

```bash
python -m venv .venv (or another name with . like .mantis)
source .venv/bin/activate    # For Windows: .venv\Scripts\activate
```

### Step 3: 📦 Install the dependencies

```bash
pip install -r requirements.txt
```

### Step 4: 🗄️ Create a PostgreSQL database

Use the Program `psql`

```bash
psql -U postgres
```

```sql
CREATE DATABASE mantis_tracker OWNER mantis_user;
CREATE USER mantis_user WITH PASSWORD 'mantis';
GRANT ALL PRIVILEGES ON DATABASE mantis_tracker TO mantis_user;
-- MacOS only:
GRANT usage, create ON SCHEMA public TO mantis_tracker;
\q
```

For pytest create a test database

```sql
CREATE DATABASE mantis_tester OWNER mantis_user;
GRANT ALL PRIVILEGES ON DATABASE mantis_tester TO mantis_user;
-- MacOS only:
GRANT usage, create ON SCHEMA public TO mantis_tester;
\q
```

> ⚠️: Only if there are any Database changes:

```bash
flask db init
```

```bash
flask db migrate -m "Define initial  database structure."
```

### Step 5: 🏗️ Create the database tables

```bash
flask db upgrade
```
### Step 6: ☕ Fill the database tables 

```bash
flask insert-initial-data
```

```bash
flask create-mview
```

### Step 7: 🎨 Run the CSS watcher

```bash
npm --proxy <your-proxy> install tailwindcss
```

```bash
npx tailwindcss -i app/static/css/theme.css -o app/static/build/theme.css --watch
```

### Step 8: 🚀 Run the development server

```bash
python run.py
```

### Step 9: 🚀 Connect as Reviewer

```bash
http://loclahost:5000/reviewer/9999
```

# Production setup

- Edit Settings in app/config.py and make changes e.g.
  - Connectionstring for DB
  - TESTING = False
  - Run Tests with pytest
  
### Step 9: 🏢 Run production server

```bash
gunicorn run:app    # For Windows: waitress-serve --listen=*:8000 run:app
```

### Step 10: 🌐 Open http://localhost:5000 in your browser

### Meldung id error fix

```bash
SELECT setval('[TableName]_id_seq', (SELECT MAX(id) FROM [TableName]))
```

