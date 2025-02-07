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

```sql
CREATE DATABASE mantis_tracker;
CREATE USER mantis_user WITH PASSWORD 'mantis';
GRANT ALL PRIVILEGES ON DATABASE mantis_tracker TO mantis_user;
-- MacOS only:
GRANT usage, create ON SCHEMA public TO mantis_user;
\q
```

> ⚠️: Only if there are any Database changes:

```bash
flask db init
```

```bash
flask db migrate -m "your comment"
```

### Step 5: 🏗️ Create the database tables

```bash
flask db upgrade
```
### Step 6: ☕ Fill the database tables 

```bash
flask create-mview
```

```bash
flask insert-initial-data
```

### Step 6: 🎨 Set up Tailwind CSS

First, install the Node.js dependencies:

```bash
cd app/static
npm install
```

The project includes a convenient script to watch for CSS changes. Start it with:

```bash
npm run watch:css
```

### Step 7: 🚀 Run the application

#### Development server

```bash
python run.py
```
This will start both the Flask development server and Tailwind CSS compiler in watch mode.

#### Production server

```bash
gunicorn run:app    # For Windows: waitress-serve --listen=*:8000 run:app
```

### Step 8: 🌐 Access the application

Open [http://localhost:5000](http://localhost:5000) in your browser.

## 🔧 Troubleshooting

### Database Sequence Reset

If you encounter issues with ID sequences, run:

```sql
SELECT setval('[TableName]_id_seq', (SELECT MAX(id) FROM [TableName]))
```

