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

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- [Bun](https://bun.sh/) or npm (for frontend dependencies)
- PostgreSQL 18+

### Step 1: 📁 Clone the repository

```bash
git clone https://gitlab.com/opendata-apps/mantis.git
cd mantis
```

### Step 2: ⚙️ Configure environment variables

```bash
# Copy the example .env file
cp .env.example .env

# Generate a secure SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Edit .env and add your SECRET_KEY
nano .env  # or your preferred editor
```

See `ENV_SETUP.md` for detailed configuration options.

### Step 3: 📦 Install dependencies

```bash
# Python dependencies (using uv)
uv sync --extra dev

# Frontend dependencies (using bun - recommended)
cd app/static && bun install

# Or use npm if you prefer
# cd app/static && npm install
```

### Step 4: 🗄️ Set up PostgreSQL database

**Requirements:** PostgreSQL 18 or higher

```bash
# Connect as postgres superuser
PGPASSWORD=postgres psql -U postgres -h localhost -d postgres
```

Then run the following SQL commands:

```sql
CREATE USER mantis_user WITH PASSWORD 'mantis';
CREATE DATABASE mantis_tracker OWNER mantis_user;
CREATE DATABASE mantis_tester OWNER mantis_user;
\q
```

**Note:** Authentication uses md5 (password-based). If you have issues, check your `pg_hba.conf` configuration.

### Step 5: 🏗️ Initialize database

```bash
# Run migrations
uv run flask db upgrade

# Populate initial data (beschreibung, feedback_types, VG5000 areas)
uv run flask insert-initial-data

# Optional: Add demo data for development
# Set TESTING=True in .env, then run insert-initial-data again
```

### Step 6: 🚀 Run the application

```bash
# Development server (includes Tailwind CSS watcher)
uv run python run.py
```

The app will be available at [http://localhost:5000](http://localhost:5000)

**Reviewer access:** [http://localhost:5000/reviewer/9999](http://localhost:5000/reviewer/9999)

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/functional/test_csrf_protection.py -v
```

## 🏭 Production Deployment

### 1. Configure production environment

Edit `.env`:
```bash
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=your-production-secret-key
SQLALCHEMY_DATABASE_URI=postgresql://mantis_user:secure_password@localhost/mantis_tracker
PREFERRED_URL_SCHEME=https
SESSION_COOKIE_SECURE=True
```

### 2. Build production CSS

```bash
cd app/static
bun run build:css  # or: npm run build:css
```

### 3. Run with production server

```bash
# Using Gunicorn (Linux/Mac)
gunicorn run:app --workers 4 --bind 0.0.0.0:8000

# Using Waitress (Windows)
waitress-serve --listen=*:8000 run:app
```

## 📚 Additional Documentation

- **Environment Setup:** See `ENV_SETUP.md` for detailed .env configuration
- **Database Schema:** Managed via Flask-Migrate in `migrations/`
- **API Endpoints:** See route blueprints in `app/routes/`

## 🔄 Database Management

```bash
# Create new migration
uv run flask db migrate -m "description"

# Apply migrations
uv run flask db upgrade

# Check current version
uv run flask db current

# Reset database (development only)
dropdb mantis_tracker && createdb mantis_tracker -O mantis_user
uv run flask db upgrade && uv run flask insert-initial-data
```
