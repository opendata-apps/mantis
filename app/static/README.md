## CSS Build

- Tailwind Input: `css/theme.css`
- Generiertes CSS: `build/theme.css`

`build/theme.css` ist ein Build-Artefakt und wird nicht manuell
bearbeitet.

Siehe infrastrukture/podman-compose.yml und
infrastrukure/README-Container-dev.org
```
+---------------------+        +------------------------+
|                     |        |                        |
|   Tailwind Service  |        |       Flask Web        |
|   (bun run watch)   |        |   (Python/Flask)       |
|                     |        |                        |
+---------+-----------+        +-----------+------------+
          |                                |
          | writes theme.css               | reads theme.css
          | to                             | from
          v                                v
   +------+------------------------+--------------------+
   |   mantis/app/static/build/theme.css (final CSS)    |
   +----------------------------------------------------+
          ^
          |
          | volume mount (optional for Dev)
          |
   +------+---------------------------+
   |  Dev-Container Host / Repo       |
   |  (source CSS in css/, templates) |
   +----------------------------------+
```