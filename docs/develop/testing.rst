Tests
=====

Überblick
---------

Die Test-Suite basiert auf Pytest und verwendet eine echte PostgreSQL-Datenbank.
Die Fixtures in ``tests/conftest.py`` migrieren und befüllen ``mantis_tester``
automatisch. ``tests/migrations`` arbeitet auf einer zweiten Datenbank,
``mantis_tester_migrations``, weil diese Tests das Schema selbst abräumen.

Voraussetzungen
---------------

- laufender PostgreSQL-Server
- Benutzer ``mantis_user`` mit ``CREATEDB``-Berechtigung
- Entwicklungsabhängigkeiten: ``uv sync``

Die Test-Datenbank ``mantis_tester`` wird automatisch erstellt und nach
Testende gelöscht. Einmalig muss ``CREATEDB`` vergeben werden:

.. code-block:: sql

   ALTER USER mantis_user CREATEDB;

Testläufe
---------

.. code-block:: bash

   uv run pytest
   uv run pytest tests/unit
   uv run pytest --cov=app --cov-report=term-missing
   bun run test

Fixture-Lebenszyklus
--------------------

- ``app`` erstellt pro Test eine Flask-App über die Produktionsfactory.
  ``test_config`` erbt die Produktionskonfiguration über ``tests.test_config.Config``.
  Tests mit abweichender Konfiguration überschreiben diese Fixture vor App-Erstellung.
- ``client`` und ``authenticated_client`` verwenden den normalen Request-Lifecycle.
  Direkte Helpertests aktivieren ``app_ctx`` oder ``request_context`` nur bei Bedarf.
- ``_schema`` legt das Schema einmal pro Testlauf an: Schema zurücksetzen,
  Alembic ausführen, Tabellennamen einsammeln.
- ``_db`` stellt vor jedem Datenbanktest den Ausgangszustand wieder her:
  ``TRUNCATE … RESTART IDENTITY CASCADE`` über diese Tabellen, dann Basisdaten
  und Demo-Meldungen neu laden. Die Ids der Demo-Daten sind dadurch in jedem
  Test dieselben. Isolation über ``TRUNCATE`` statt über ein Rollback, weil
  HTTP- und CLI-Aufrufe auf einer eigenen Verbindung wirklich committen —
  dasselbe Vorgehen wie Djangos ``TransactionTestCase``.
- ``session`` verwendet eine eigene Datenbankverbindung. Testdaten für HTTP-
  oder CLI-Aufrufe benötigen ``commit()``. Ein ``flush()`` ist nur innerhalb
  derselben Transaktion sichtbar. Die Anwendung verwendet unverändert ``db.session``.
- Uploads und Backups liegen pro Test unter ``tmp_path``. Unveränderte Favicons
  werden einmal je Testlauf in einem gemeinsamen temporären Verzeichnis erzeugt.
- Migrationstests verwalten ihren Schemaaufbau selbst und laufen dafür gegen
  ``mantis_tester_migrations``. Beide Datenbanken werden nach Testende
  gelöscht. Datenbanktests laufen seriell.
- Ein zweiter gleichzeitiger Testlauf bricht sofort ab. ``_exclusive_run`` hält
  dafür ein ``pg_advisory_lock`` auf der Wartungsdatenbank. Ohne den Riegel
  zeigt sich ein zweiter Schreiber als Deadlock, doppelter Primärschlüssel oder
  verschwundene Tabelle — hunderte Tests hinter der Ursache.

Konventionen
------------

Grundlage ist Googles `Test Behavior, Not Implementation
<https://testing.googleblog.com/2013/08/testing-on-toilet-test-behavior-not.html>`_
und das Testkapitel von *Software Engineering at Google*. Ein Test schlägt fehl,
wenn sich das Verhalten ändert — und nur dann. Ein Refactoring, das Verhalten
erhält, darf keinen Test brechen.

1. **Ein Test pro Verhalten, nicht pro Methode.** Der Name nennt Bedingung und
   Erwartung: ``test_a_partial_place_name_finds_the_same_reports``, nicht
   ``test_search``. Innerhalb einer Datei ist jeder Name eindeutig, sonst sagt
   der Fehlerbericht nicht, welcher Fall gebrochen ist.
2. **Erwartungswerte kommen von außen.** Aus dem Blattschnitt, der
   Spezifikation, einer Handrechnung — nie aus der Implementierung und nie über
   dieselbe Formel berechnet, die der Code verwendet. Das MTB-Gitter stand
   achtzehn Monate falsch, weil die Erwartungswerte aus dem Code abgelesen und
   mit dem Kommentar ``# Potsdam - corrected`` auf den falschen Wert gesetzt
   worden waren.
3. **Zusichern auf Antwort und gespeichertem Zustand.** Kein
   ``assert_called_once`` auf eine eigene Funktion: das wiederholt den Code,
   statt ihn zu prüfen. Ein ``populate_all``, das nichts schreibt, erfüllt eine
   solche Zusicherung.
4. **Ersetzt wird nur die Prozessgrenze.** SMTP, HTTP, ``subprocess``,
   Dateisystem außerhalb ``tmp_path``. Eigene private Helfer werden nicht
   gepatcht — dann testet der Test die Verdrahtung, nicht die Funktion.
5. **Jeder Test besitzt seine Daten.** Werte und Ids aus dem Demo-Seed sind
   keine Zusicherung; sie brechen, wenn sich der Seed ändert, und beweisen
   nichts über die Aggregation. Der Test schreibt die Zeilen, über die er
   urteilt (Beispiel: ``counted_reports`` in ``tests/statistics/conftest.py``).
6. **Keine Zusicherung nur in einer Schleife oder einem Zweig.** Sonst ist der
   Test grün, wenn die Menge leer ist — und genau das ist der Ausfall, der
   auffallen müsste. Stattdessen die ganze Menge vergleichen
   (``assert ids == {8, 18}``) oder ``@pytest.mark.parametrize`` verwenden, das
   jeden Fall einzeln meldet.
7. **Größe statt Schicht.** Ohne Datenbank und ohne Ein-/Ausgabe ist ein Test
   klein und läuft in Millisekunden; braucht er ``session`` oder ``client``,
   kostet er den Datenreset. Eine reine Funktion bekommt keine
   Datenbank-Fixture.
8. **DAMP vor DRY.** Ein wiederholter Aufbau im Test ist billiger als eine
   Indirektion, die den geprüften Fall verbirgt. Kommentare in Tests sind das
   Szenario, nicht der Code.

Als Vorlage dienen ``tests/functional/test_reviewer_search.py``,
``tests/functional/test_reporter_ownership.py`` und
``TestFilterStatusNormalisation`` in
``tests/functional/test_is_comparison_filters.py``.

Durchgesetzt wird der mechanisch prüfbare Teil über ``ruff check``: der
Regelsatz ``PT`` (flake8-pytest-style), ``argnames`` als ``"a,b"`` wie in der
Pytest-Dokumentation, und ``F811`` meldet einen Testnamen, der in derselben
Datei oder Klasse zweimal definiert ist (Regel 1). Die übrigen Regeln trägt der
Review: welche Schleife leer sein kann und woher ein Erwartungswert stammt,
erkennt keine statische Analyse.

Verifikation und Referenzen
----------------------------

``tests/config/test_application_context.py`` prüft Kontextabbau,
Konfigurationsisolation und temporäre Schreibverzeichnisse.
``tests/config/test_testing_config.py`` vergleicht die geladene App-Konfiguration
mit den Produktionsvorgaben und prüft Cookie-Flags am echten Login.
``tests/config/test_database_isolation.py`` prüft reale Commits, Rollbacks
und den Reset zwischen Tests. Verhalten wird über Antworten und gespeicherte
Ergebnisse geprüft. Netzwerkzugriffe werden an der externen Schnittstelle ersetzt.

Die App-Factory und App pro Test folgen den
`Flask-Testfixtures <https://flask.palletsprojects.com/en/stable/testing/#fixtures>`_
und `Cookiecutter-Flask <https://github.com/cookiecutter-flask/cookiecutter-flask/blob/e5666c23a633b5b6fcb0dc2cfda2441d7f885727/%7B%7Bcookiecutter.app_name%7D%7D/tests/conftest.py>`_.
Cookiecutters globaler Request-Kontext wird nicht übernommen.
Für Kontextgrenzen gilt die aktuelle
`Flask-SQLAlchemy-Dokumentation <https://flask-sqlalchemy.palletsprojects.com/en/stable/contexts/#tests>`_.
PostgreSQL und Alembic bleiben notwendig, weil die Tests auch Trigger,
Volltextsuche, ``CHECK``-Constraints und die View ``all_data_view`` prüfen.

Pytest-Optionen stehen in ``pyproject.toml``. Die Standardoption ``-l`` zeigt
lokale Variablen. Kein ``-x``: ein Defekt in der gemeinsamen Datenbank-Fixture
lässt jeden folgenden Test scheitern, und der erste dieser Fehler sagt nichts
über die Ursache.
