# 🦗 Mantis Tracker 🦗

![Header Banner](https://i.ibb.co/fxgcjgC/image-2023-05-02-210757973.png)

An interactive web application to track Mantis Religiosa sightings in Brandenburg, presented by the Naturkunde Museum Potsdam.

Mantis Tracker allows users to report Mantis Religiosa sightings and view them on an interactive map, along with insightful statistics and helpful FAQs.

## 🌟 Features

- 📚 Learn about the Mantis Religiosa
- 🎨 Beautiful UI
- 📝 Report mantis sightings with an easy-to-use form
- 🗺️ View all mantis sightings on an interactive map
- 📊 View insightful statistics and FAQs

## 🛠️ Technologies

![HTML](https://img.shields.io/badge/-HTML-000000?style=flat&logo=HTML5)
![CSS](https://img.shields.io/badge/-CSS-000000?style=flat&logo=CSS3&logoColor=1572B6)
![Jinja2](https://img.shields.io/badge/-Jinja2-000000?style=flat&logo=jinja)
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

Verwenden sie das Programm `psql` für ihr Betriebssystem.

```bash
psql -U postgres
```

```sql
CREATE DATABASE mantis_tracker;
CREATE USER mantis_user WITH PASSWORD 'mantis';
GRANT ALL PRIVILEGES ON DATABASE mantis_tracker TO mantis_user;
\q
```

### Step 5: 🔄 ONLY If database structure changed

```bash
flask db init
```

```bash
flask db migrate -m "your comment"
```

### Step 6: 🏗️ Create the database tables

```bash
flask db upgrade
```

### Step 7: 📈 Import Data

```bash
\copy plzort(plz, ort, bundesland, landkreis) FROM 'C:\home\mantis\app\database\ww-german-postal-codes.csv' WITH (FORMAT csv, DELIMITER ',', HEADER true, ENCODING 'utf-8')
```

### Step 8: 🎨 Run the CSS watcher

```bash
npm --proxy <your-proxy> install tailwindcss
```

```bash
npx tailwindcss -i app/static/css/theme.css -o app/static/build/theme.css --watch
```

### Step 9: 🚀 Run the development server

```bash
python run.py
```

### Step 10: 🏢 Run production server

```bash
gunicorn run:app    # For Windows: waitress-serve --listen=*:8000 run:app
```

### Step 11: 🌐 Open http://localhost:5000 in your browser

### Meldung id error fix

```bash
SELECT setval('[TableName]_id_seq', (SELECT MAX(id) FROM [TableName]))
```

# 📝 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
