PROJECT_NAME=mantis

help:
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## ' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Production
prod-up: ## Start production containers
	podman-compose -f podman-compose.prod.yml up -d --build

prod-down: ## Stop production containers
	podman-compose -f podman-compose.prod.yml down

prod-logs: ## View production logs
	podman-compose -f podman-compose.prod.yml logs -f

# Development
dev-up: ## Start dev containers (with hot-reload)
	podman-compose -f podman-compose.prod.yml -f podman-compose.dev.yml up --build

dev-down: ## Stop dev containers
	podman-compose -f podman-compose.prod.yml -f podman-compose.dev.yml down

dev-logs: ## View dev logs
	podman-compose -f podman-compose.prod.yml -f podman-compose.dev.yml logs -f

# Utilities
clean: ## Remove containers and volumes
	podman-compose -f podman-compose.prod.yml down -v

shell-web: ## Shell into web container
	podman exec -it $(PROJECT_NAME)-web /bin/bash

shell-db: ## Connect to database
	podman exec -it $(PROJECT_NAME)-db psql -U mantis_user -d mantis_tracker

ps: ## List running containers
	podman-compose -f podman-compose.prod.yml ps
