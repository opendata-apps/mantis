"""Gunicorn configuration, loaded via --config in entrypoint.sh."""

bind = "0.0.0.0:5000"
workers = 4
# threads > 1 makes gunicorn swap the sync worker for gthread on its own
# (Config.worker_class), so worker_class stays unset on purpose.
threads = 2
# tmpfs, not the default temp dir: the heartbeat calls os.fchmod on a file here
# and gunicorn documents that as able to block a worker for arbitrary time when
# the directory is disk-backed.
worker_tmp_dir = "/dev/shm"
# "-" is stdout/stderr, which is what puts request logs into journalctl.
accesslog = "-"
errorlog = "-"


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
