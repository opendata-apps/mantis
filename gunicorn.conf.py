"""Gunicorn configuration, loaded via --config in the Dockerfile's CMD."""

bind = "0.0.0.0:5000"
workers = 4
# threads > 1 makes gunicorn swap the sync worker for gthread on its own
# (Config.worker_class), so worker_class stays unset on purpose.
threads = 2
# Must stay on a tmpfs. The heartbeat calls os.fchmod on a file in here, which
# gunicorn's own worker_tmp_dir setting documents as able to block a worker for
# arbitrary time when the directory is disk-backed.
worker_tmp_dir = "/dev/shm"
# Keep both on the streams. Pointing either at a file takes the request log out
# of `journalctl _UID=1002`, which is the only place we read it from.
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(t)s "%(m)s %({mantis.route}e)s" %(s)s %(b)s %(L)s'


def post_worker_init(worker):
    """Build the polygon cache before the worker serves traffic.

    Otherwise each worker's first /melden/ags-lookup waits ~1.8 s for it.
    """
    from app.tools.gemeinde_finder import warm_gemeinde_cache

    with worker.wsgi.app_context():
        warm_gemeinde_cache()
