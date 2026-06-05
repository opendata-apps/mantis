"""Gunicorn configuration, loaded via --config in entrypoint.sh."""


def post_worker_init(worker):
    """Warm per-worker caches after app load, before the worker serves traffic.

    gunicorn runs this hook after load_wsgi() (gunicorn/workers/base.py), so
    worker.wsgi is the loaded Flask app. Without it, the first
    /melden/ags-lookup request hitting each worker pays the full polygon-cache
    build (~1.8s in production) while the report form's address fields are
    locked.
    """
    from app.tools.gemeinde_finder import warm_gemeinde_cache

    with worker.wsgi.app_context():
        warm_gemeinde_cache()
