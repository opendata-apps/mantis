# Mantis Dokumentation (DE)

Einstiegsseite für die Dokumentation.

## Aktuelle Einstiege

- Projekt-Setup und tägliche Kommandos: [`README.md`](../README.md)
- Sphinx-Dokumentation (Benutzer + Technik): [`docs/index.rst`](./index.rst)
- Technische Übersicht: [`docs/develop/index.rst`](./develop/index.rst)

## Dokumentation lokal bauen

```bash
uv sync --extra docs
make -C docs html
```
