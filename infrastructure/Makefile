# Projekt-Name
PROJECT_NAME=mantis

help:
	@echo "Verfügbare Make-Kommandos:"
	@grep -E '^[a-zA-Z_-]+:.*?## ' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Standardbefehle
up: ## Startet die Container im Hintergrund
	podman-compose up -d --build

down: ## Stoppt und entfernt die Container
	podman-compose down

restart: down up

logs: ## Logs ausgeben
	podman-compose logs -f

build: ## neu erstellen
	podman-compose build

ps: ## Liste der Container
	podman-compose ps

sh-web: ## interaktiv in den Web-Container
	podman exec -it $(PROJECT_NAME)-web /bin/sh

sh-db: ## interaktiv in den Datenbank-Container
	podman exec -it $(PROJECT_NAME)-db psql -U app -d appdb

clean: ## alles löschen als Vorbereiung für neues build
	podman-compose down -v
