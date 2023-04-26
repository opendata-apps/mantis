# Mantis

A Project from the Naturkunde Museum Potsdam to track the Mantis Religiosa in Brandenburg.

Mantis Report is a web application that allows users to report sightings of the Mantis Religiosa in Brandenburg and display them on an interactive map.

## Features

- Information about the mantis
- good looking UI
- Report mantis sightings with a form
- View all mantis sightings on an interactive map
- View statistics and FAQs

## Technologies

- HTML
- CSS
- Jinja2
- Python
- Flask
- PostgreSQL(Version 14)
- Tailwind CSS
- JavaScript

![HTML](https://img.shields.io/badge/-HTML-000000?style=flat&logo=HTML5)
![CSS](https://img.shields.io/badge/-CSS-000000?style=flat&logo=CSS3&logoColor=1572B6)
![Jinja2](https://img.shields.io/badge/-Jinja2-000000?style=flat&logo=jinja)
![Python](https://img.shields.io/badge/-Python-000000?style=flat&logo=python)
![Flask](https://img.shields.io/badge/-Flask-000000?style=flat&logo=flask)
![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-000000?style=flat&logo=postgresql)
![Tailwind CSS](https://img.shields.io/badge/-Tailwind%20CSS-000000?style=flat&logo=tailwind-css)
![JavaScript](https://img.shields.io/badge/-JavaScript-000000?style=flat&logo=javascript)

## Development Setup/Installation 

```bash
# Clone the repository
git clone https://gitlab.com/opendata-apps/mantis.git
cd mantis_flask

# Create a virtual environment and activate it
python -m venv venv
source venv/bin/activate

# Install the dependencies
pip install -r requirements.txt

# Create a PostgreSQL database (Verion 14)
sudo -u postgres psql
CREATE DATABASE mantis_tracker;
CREATE USER mantis_user WITH PASSWORD 'mantis';
GRANT ALL PRIVILEGES ON DATABASE mantis_tracker TO mantis_user;
\q

# Create the database tables
flask db upgrade

# Run the CSS watcher
npx tailwindcss -i app/static/css/theme.css -o app/static/build/theme.css --watch

# Run the development server
flask run

# Open http://localhost:5000 in your browser
 



```


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

