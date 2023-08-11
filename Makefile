PROJEKT   = mantis
ENV = .env
SHELL := /bin/bash

.PHONY: setup
setup:
	mkdir "$(PROJEKT)" && cd $(PROJEKT)  && python3 -m venv "$(ENV)" && source "$(ENV)"/bin/activate && pip install -r requirements.txt

.PHONY: lint
lint:
	source "$(ENV)/bin/activate" && flake8  tests app

.PHONY: routes
routes:
	source "$(ENV)/bin/activate" && flask routes

.PHONY: run
run:
	source "$(ENV)"/bin/activate && flask run

.PHONY: cov
cov:
	source "$(ENV)"/bin/activate && pytest --cov=emojisearcher --cov-report=term-missing --cov-fail-under=80

.PHONY: help
help:
	@echo "Alle Optionen:"
	@echo "=============="
	@echo ""
	@echo "setup  -- erstellt ein neues Projekt, mit virtuellem Environment"
	@echo "lint   -- Validierung der Syntax"
	@echo "routes -- Alle Routen der Flask-App"
	@echo "run    -- Flask-App starten"	
	@echo "cov    -- Test-Abdeckung"
	@echo "help   -- dieser Text"
