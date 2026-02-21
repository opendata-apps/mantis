# Static Assets

## Verzeichnisstruktur

```text
app/static/
├── css/
│   └── theme.css          # Tailwind v4 + @theme Tokens
├── js/
│   ├── vendor.js
│   ├── map.js
│   ├── report-form-htmx.js
│   ├── admin-htmx.js
│   ├── admin-modal.js
│   └── ...
├── build/                 # Vite-Buildausgabe (nicht manuell bearbeiten)
├── images/
├── robots.txt
└── sitemap.xml
```

## Build-Kommandos

Aus Projektwurzel:

```bash
bun install
bun run build
bun run watch
```

## Laufzeitintegration

- Flask lädt Assets über Helper aus `app/tools/vite.py`.
- Produktionspfade werden über `build/.vite/manifest.json` aufgelöst.
- Templates verwenden `vite_asset(...)` bzw. `vite_tags(...)`.

## Wichtige Hinweise

- Dateien unter `app/static/build` sind Build-Artefakte.
- Token/Farbänderungen erfolgen in `app/static/css/theme.css`.
- Nach Änderungen an JS-Entry-Points oder CSS-Tokens Build erneut ausführen.
