Deployment hinter Nginx
=======================

Die Anwendung ist für den Betrieb hinter einem Reverse Proxy vorbereitet.
``ProxyFix`` ist in ``app/__init__.py`` bereits aktiviert:

.. code-block:: python

   from werkzeug.middleware.proxy_fix import ProxyFix

   app.wsgi_app = ProxyFix(
       app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
   )

WSGI-Start
----------

Produktionsstart erfolgt typischerweise mit Gunicorn:

.. code-block:: bash

   gunicorn run:app -c gunicorn_config.py

Minimale Nginx-Konfiguration
----------------------------

.. code-block:: nginx

   server {
       server_name example.com;

       location / {
           proxy_pass http://127.0.0.1:5000/;
           proxy_set_header Host $host;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_set_header X-Forwarded-Host $host;
           proxy_set_header X-Forwarded-Prefix /;
       }
   }

Empfohlene Ergänzungen
----------------------

- TLS-Termination in Nginx
- ``proxy_read_timeout`` passend zu erwarteter Last
- Zugriff auf ``/health`` für externe Healthchecks
- Logging und Rotation auf Nginx- und Gunicorn-Ebene

Weitere Hinweise in der Flask-Dokumentation:
`Tell Flask it is Behind a Proxy`_.

.. _Tell Flask it is Behind a Proxy: https://flask.palletsprojects.com/en/stable/deploying/proxy_fix/
