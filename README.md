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
- 🖼️ Photo gallery of Mantis Religiosa

## 🛠️ Technologies

![HTML](https://img.shields.io/badge/-HTML-000000?style=flat&logo=HTML5)
![CSS](https://img.shields.io/badge/-CSS-000000?style=flat&logo=CSS3&logoColor=1572B6)
![Jinja2](https://img.shields.io/badge/-Jinja2-000000?style=flat&logo=jinja)
![Python](https://img.shields.io/badge/-Python-000000?style=flat&logo=python)
![Flask](https://img.shields.io/badge/-Flask-000000?style=flat&logo=flask)
![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-000000?style=flat&logo=postgresql)
![Tailwind CSS](https://img.shields.io/badge/-Tailwind%20CSS-000000?style=flat&logo=tailwind-css)
![JavaScript](https://img.shields.io/badge/-JavaScript-000000?style=flat&logo=javascript)

# 💻 Development Setup

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- [Bun](https://bun.sh/) (for frontend dependencies)
- PostgreSQL 16+

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

# Frontend dependencies
bun install

# Build frontend assets (JS bundles + CSS)
bun run build
```

### Step 4: 🗄️ Set up PostgreSQL database

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

### Step 5: 🏗️ Initialize database

```bash
# Run migrations
uv run flask db upgrade

# Create materialized views
uv run flask create_all_data_view

# Populate initial data (beschreibung, feedback_types, VG5000 areas)
uv run flask seed

# Optional: Add demo data for development
uv run flask seed --demo
```

### Step 6: 🚀 Run the application

```bash
# Development server (includes Vite build watcher for CSS/JS)
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

## 🐳 Container Deployment

### Production

```bash
cd infrastructure

# Build and start containers
podman-compose -f podman-compose.prod.yml up -d --build

# View logs
podman-compose -f podman-compose.prod.yml logs -f

# Stop containers
podman-compose -f podman-compose.prod.yml down
```

### Development (with hot-reload)

```bash
cd infrastructure

# Start with dev overlay (mounts source, enables debug mode)
podman-compose -f podman-compose.prod.yml -f podman-compose.dev.yml up --build

# This gives you:
# - Flask debug mode with auto-reload
# - Vite build watcher (CSS/JS)
# - Source code mounted for live editing
```

### Container Environment

For container deployment, update `.env`:
```bash
SQLALCHEMY_DATABASE_URI=postgresql://mantis_user:mantis@db:5432/mantis_tracker
```

The container setup includes:
- **PostgreSQL 16** database with health checks
- **Flask app** with auto-migrations on startup
- **Volume mount** for uploaded images (`datastore/`)

## 🏭 Production Deployment (Manual)

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

### 2. Build production assets

```bash
bun run build
```

### 3. Run with production server

```bash
# Using Gunicorn (Linux/Mac)
gunicorn run:app --workers 4 --bind 0.0.0.0:8000

# Using Waitress (Windows)
waitress-serve --listen=*:8000 run:app
```

## 📁 Project Structure

```
mantis/
├── app/                    # Flask application
│   ├── routes/             # Route blueprints
│   ├── database/           # SQLAlchemy models
│   ├── templates/          # Jinja2 templates
│   ├── static/             # Static assets
│   │   ├── js/             # JavaScript source files
│   │   ├── css/            # CSS source files
│   │   └── build/          # Built assets (generated)
│   └── tools/              # Utility modules
├── datastore/              # Uploaded images (gitignored)
├── infrastructure/         # Container configs
├── migrations/             # Database migrations
└── tests/                  # Test suite
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
uv run flask db upgrade && uv run flask create_all_data_view && uv run flask seed
```
