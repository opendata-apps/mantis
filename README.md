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

Key settings in `.env`:
- `SECRET_KEY` - Required for session security
- `SQLALCHEMY_DATABASE_URI` - Database connection (use `@localhost` for local, `@db` for containers)
- `FLASK_ENV` - Set to `development` or `production`

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

### Understanding the Setup

This project uses a **two-file overlay pattern**:
- `podman-compose.prod.yml` - Base production config (Gunicorn + PostgreSQL)
- `podman-compose.dev.yml` - Development overrides (hot-reload + Vite watcher)

| Aspect | Production | Development |
|--------|------------|-------------|
| Server | Gunicorn (2 workers) | Flask dev server |
| Frontend | Pre-built in image | Live Vite watcher |
| Code changes | Requires rebuild | Hot-reloaded |
| Services | db + web | db + web + vite |

### Before Running Containers

Update `.env` to use container networking:
```bash
# Change @localhost to @db (the container service name)
SQLALCHEMY_DATABASE_URI=postgresql://mantis_user:mantis@db:5432/mantis_tracker
```

### Production

```bash
cd infrastructure

# Build and start
podman-compose -f podman-compose.prod.yml up -d --build

# View logs
podman-compose -f podman-compose.prod.yml logs -f

# Stop
podman-compose -f podman-compose.prod.yml down
```

### Development (with hot-reload)

```bash
cd infrastructure

# Start with dev overlay
podman-compose -f podman-compose.prod.yml -f podman-compose.dev.yml up --build

# This gives you:
# - Flask debug mode with auto-reload on Python changes
# - Vite watcher rebuilding CSS/JS on file changes
# - Source code mounted from host
```

### What Happens on Startup

1. PostgreSQL starts and waits for health check
2. Flask runs migrations automatically (`flask db upgrade`)
3. Materialized views are created (`flask create_all_data_view`)
4. Database is seeded (demo data in dev mode)
5. Gunicorn (prod) or Flask dev server (dev) starts

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

## 📚 Additional Information

- **Environment Variables:** See `.env.example` for all available settings
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
