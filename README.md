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

## 🚀 Quick Start (Containers)

Prerequisites: [Podman](https://podman.io/) (or Docker), [just](https://github.com/casey/just)

```bash
git clone https://gitlab.com/opendata-apps/mantis.git
cd mantis
cp .env.example .env
# Set SECRET_KEY in .env (generate with: python -c "import secrets; print(secrets.token_hex(32))")
just up --build
```

The app will be available at [http://localhost:5000](http://localhost:5000)

On startup, the container automatically runs migrations, creates materialized views, and seeds the database. In dev mode (`FLASK_ENV=development`), demo data is included.

### Available Commands

```
just up *ARGS        Start dev environment (hot-reload + Vite)
just down *ARGS      Stop dev environment
just build *ARGS     Build dev containers
just logs *ARGS      Show container logs
just shell           Open bash shell in web container
just db              Open psql shell in db container
just migrate *ARGS   Run database migrations
just seed *ARGS      Seed base data
just prod *ARGS      Start production (Gunicorn, detached)
just prod-down *ARGS Stop production
```

### Production

Set these in `.env` before deploying:

```bash
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=<generated-key>          # required, app refuses to start without it
POSTGRES_PASSWORD=<secure-password>
PREFERRED_URL_SCHEME=https
SESSION_COOKIE_SECURE=True
```

Then: `just prod --build`

<details>
<summary><strong>Without just (manual setup & compose commands)</strong></summary>

```bash
# First-time setup
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
# Paste the output as SECRET_KEY= in .env

# Dev
podman-compose -f infrastructure/podman-compose.prod.yml -f infrastructure/podman-compose.dev.yml up --build
podman-compose -f infrastructure/podman-compose.prod.yml -f infrastructure/podman-compose.dev.yml down

# Production
podman-compose -f infrastructure/podman-compose.prod.yml up --build -d
podman-compose -f infrastructure/podman-compose.prod.yml down
```

</details>

<details>
<summary><h2>💻 Local Development (without containers)</h2></summary>

Prerequisites: Python 3.13+, [uv](https://github.com/astral-sh/uv), [Bun](https://bun.sh/), PostgreSQL 16+

### Setup

```bash
cp .env.example .env
# Set SECRET_KEY in .env

uv sync --extra dev
bun install
bun run build
```

### Database

```sql
-- As postgres superuser:
CREATE USER mantis_user WITH PASSWORD 'mantis';
CREATE DATABASE mantis_tracker OWNER mantis_user;
CREATE DATABASE mantis_tester OWNER mantis_user;
```

```bash
uv run flask db upgrade
uv run flask create_all_data_view
uv run flask seed          # base data
uv run flask seed --demo   # optional: demo data
```

### Run

```bash
uv run python run.py
```

</details>

## 🧪 Testing

```bash
uv run pytest
uv run pytest --cov=app --cov-report=html
uv run pytest tests/functional/test_csrf_protection.py -v
```

## 📁 Project Structure

```
mantis/
├── app/                    # Flask application
│   ├── routes/             # Route blueprints
│   ├── database/           # SQLAlchemy models
│   ├── templates/          # Jinja2 templates
│   ├── static/             # Static assets (js/, css/, build/)
│   └── tools/              # Utility modules
├── infrastructure/         # Container configs (compose files)
├── migrations/             # Alembic database migrations
└── tests/                  # Test suite
```

## 📚 Additional Information

- **Environment Variables:** See `.env.example` for all available settings
- **Database Schema:** Managed via Flask-Migrate in `migrations/`
- **API Endpoints:** See route blueprints in `app/routes/`
