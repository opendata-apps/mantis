.PHONY: help up down logs build clean shell-web shell-db up-prod down-prod logs-prod

COMPOSE_DEV  := podman-compose -f podman-compose.prod.yml -f podman-compose.dev.yml
COMPOSE_PROD := podman-compose -f podman-compose.prod.yml

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

up: ## Start dev environment
	$(COMPOSE_DEV) up -d --build

down: ## Stop dev environment
	$(COMPOSE_DEV) down

logs: ## View dev logs
	$(COMPOSE_DEV) logs -f

up-prod: ## Start production
	$(COMPOSE_PROD) up -d --build

down-prod: ## Stop production
	$(COMPOSE_PROD) down

logs-prod: ## View production logs
	$(COMPOSE_PROD) logs -f

build: ## Build images
	$(COMPOSE_PROD) build

clean: ## Remove containers and volumes
	$(COMPOSE_PROD) down -v --remove-orphans

shell-web: ## Shell into web container
	podman exec -it infrastructure_web_1 /bin/bash

shell-db: ## Connect to database
	podman exec -it infrastructure_db_1 psql -U mantis_user -d mantis_tracker
