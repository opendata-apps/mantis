===============
 Server: Nginx
===============

Eine Flask-Anwendung hinter einem Proxy (NGINX) zu platzieren,
erfordert zusätzliche Konfigurationsschritte wie hier beschrieben:

`Flask hinter NGINX`_

::

   from werkzeug.middleware.proxy_fix import ProxyFix
   
   app.wsgi_app = ProxyFix(
        app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
    )

Die NGINX-Konfiguration:

::

   server {
     server_name example.com;

    location / {
        proxy_pass http://127.0.0.1:8080/;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Prefix /;

   }
   
.. _Flask hinter NGINX: https://flask.palletsprojects.com/en/2.3.x/deploying/proxy_fix/ 


