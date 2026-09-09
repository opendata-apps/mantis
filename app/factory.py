import os
import tomllib
from datetime import datetime
from pathlib import Path

import pillow_heif
from flask import Flask, jsonify, render_template, request
from PIL import Image
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config
from .extensions import csrf, db, flask_favicon, limiter, mail, migrate

with (Path(__file__).resolve().parent.parent / "pyproject.toml").open(
    "rb"
) as _pyproject:
    __version__ = tomllib.load(_pyproject)["project"]["version"]


def create_app(config_class=Config) -> Flask:
    # Must be the bare package, not "app.factory" (cookiecutter-flask does the
    # same). Flask names its logger after the import name, and app/tools/* log
    # through logging.getLogger(__name__); only an "app" logger is an ancestor
    # of those, so only it passes down the level set in configure_logger and
    # Flask's handler. Under "app.factory" they fall back to root/WARNING and
    # drop out of the logs. Template and static roots are unaffected either
    # way — factory.py already sits in app/.
    app = Flask(__name__.split(".")[0])
    app.config.from_object(config_class)

    # Logging first, so every step below can log. The rest is grouped the way
    # cookiecutter-flask groups it; the order of these calls is the wiring
    # order, so read them top to bottom.
    configure_logger(app)
    register_heif_opener()
    register_extensions(app)
    register_template_globals(app)

    from app.cli import register_commands

    register_commands(app)

    register_shellcontext(app)
    configure_middlewares(app)
    register_blueprints(app)
    register_errorhandlers(app)

    return app


def configure_logger(app: Flask) -> None:
    """No file handler: RotatingFileHandler is documented as single-process, and
    every gunicorn worker builds its own, so a rollover renames the file out
    from under the others and lines are lost. Flask's own handler writes to
    stderr, which the container hands to journald — the log we actually read.
    """
    if not app.debug:
        app.logger.setLevel(os.environ.get("FLASK_LOG_LEVEL", "INFO").upper())
        app.logger.info("Mantis tracker startup")


def register_heif_opener() -> None:
    """HEIC/HEIF decoding for iPhone uploads.

    Registers a plugin into Pillow's own opener table, so `Image.open` handles
    HEIC and the existing WebP re-encode path needs no change. Verified rather
    than assumed: registration silently no-ops against an incompatible Pillow,
    which would turn every HEIC upload into a 500 at runtime instead of here.
    https://github.com/bigcat88/pillow_heif/issues/340
    """
    pillow_heif.register_heif_opener()
    if "HEIF" not in Image.OPEN:
        raise RuntimeError(
            "pillow-heif did not register a HEIF opener; HEIC uploads would fail"
        )


def register_extensions(app: Flask) -> None:
    csrf.init_app(app)
    db.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    flask_favicon.init_app(app)

    flask_favicon.register_favicon("app/static/images/logo.png", "default")

    migrate.init_app(app, db)

    from app.tools import vite

    vite.init_app(app)


def register_template_globals(app: Flask) -> None:
    # Heroicons — usage: {{ heroicon_outline("map-pin", class="w-4 h-4") }}
    from heroicons.jinja import heroicon_mini, heroicon_outline

    app.jinja_env.globals.update(
        {
            "heroicon_mini": heroicon_mini,
            "heroicon_outline": heroicon_outline,
        }
    )

    @app.context_processor
    def inject_now():
        return {"now": datetime.now(), "version": __version__}


def register_shellcontext(app: Flask) -> None:
    @app.shell_context_processor
    def make_shell_context():
        from app.database.models import TblFundorte, TblMeldungen, TblUsers

        return {
            "db": db,
            "TblMeldungen": TblMeldungen,
            "TblUsers": TblUsers,
            "TblFundorte": TblFundorte,
        }


def configure_middlewares(app: Flask) -> None:
    """Order matters here: Flask runs after_request handlers in reverse
    registration order, so add_security_headers below runs last and has the
    final say on the headers.
    """
    # Only apply ProxyFix when behind a reverse proxy (e.g. Nginx).
    # Applying unconditionally lets clients forge X-Forwarded-For headers.
    # https://flask.palletsprojects.com/en/stable/deploying/proxy_fix/
    if not app.debug:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        # Explicitly off, not absent: OWASP Secure Headers asks for "0" so a
        # legacy browser cannot fall back to its own buggy XSS auditor.
        response.headers["X-XSS-Protection"] = "0"
        if app.config.get("PREFERRED_URL_SCHEME") == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        # Content Security Policy. `script-src` deliberately omits
        # 'unsafe-eval' — htmx's eval-based features are gated off via
        # `htmx.config.allowEval = false` in every JS entrypoint.
        # 'unsafe-inline' is still required for the remaining inline
        # `onclick=` handlers and `<script>` blocks.
        # TODO: move those to delegated listeners so 'unsafe-inline' can go.
        # 'wasm-unsafe-eval' is what lets the report form's HEIC decoder
        # (heic2any = libheif compiled to wasm) compile at all; without it
        # every HEIC upload hangs. It permits WebAssembly only — not JS eval.
        # `worker-src 'self' blob:` — canvas-confetti spawns its render
        # worker via URL.createObjectURL(new Blob(...)) for performance.
        response.headers["Content-Security-Policy"] = "; ".join(
            [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'",
                "style-src 'self' 'unsafe-inline'",
                "worker-src 'self' blob:",
                (
                    "img-src 'self' data: blob: "
                    "https://i.creativecommons.org "
                    "https://tile.openstreetmap.org "
                    "https://*.tile.openstreetmap.org "
                    "https://server.arcgisonline.com"
                ),
                (
                    "connect-src 'self' "
                    "https://nominatim.openstreetmap.org "
                    "https://tile.openstreetmap.org "
                    "https://*.tile.openstreetmap.org "
                    "https://server.arcgisonline.com"
                ),
                "font-src 'self' data:",
                "object-src 'none'",
                "base-uri 'self'",
                "frame-ancestors 'none'",
                "form-action 'self'",
            ]
        )
        return response

    # HTMX error recovery middleware
    # When an HTMX request hits an auth/CSRF denial, the default HTMX 2.0
    # behavior (swap:false for 4xx) causes silent failure — the user gets
    # no feedback. Adding HX-Redirect tells HTMX to do a full-page
    # navigation to a recovery URL instead.
    # Pattern: https://www.wimdeblauwe.com/blog/2022/10/04/htmx-authentication-error-handling/
    @app.after_request
    def htmx_error_redirect(response):
        if request.headers.get("HX-Request") == "true" and response.status_code == 403:
            response.headers["HX-Redirect"] = "/"
        return response


def register_blueprints(app: Flask) -> None:
    from app.routes.admin import admin
    from app.routes.backup import backup
    from app.routes.data import data
    from app.routes.main import main
    from app.routes.provider import provider
    from app.routes.regionen import regionen
    from app.routes.report import report
    from app.routes.statistics import stats

    app.register_blueprint(main)
    app.register_blueprint(admin)
    app.register_blueprint(backup)
    app.register_blueprint(data)
    app.register_blueprint(stats)
    app.register_blueprint(provider)
    app.register_blueprint(regionen)
    app.register_blueprint(report)

    # Reviewers work through admin in bursts; the default limits are aimed at
    # anonymous reporters.
    limiter.exempt(admin)


def register_errorhandlers(app: Flask) -> None:
    from flask_wtf.csrf import CSRFError

    app.register_error_handler(404, page_not_found)
    app.register_error_handler(403, forbidden)
    app.register_error_handler(429, too_many_requests)
    app.register_error_handler(500, internal_server_error)

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        app.logger.warning(f"CSRF error: {e!s}")
        return render_template("error/403.html"), 403


def wants_json_response():
    """Check if the client prefers a JSON response (AJAX/API calls)."""
    best = request.accept_mimetypes.best_match(["application/json", "text/html"])
    return best == "application/json"


def page_not_found(e):
    from flask import current_app

    current_app.logger.warning(
        f"Page not found: {request.url} - User Agent: {request.headers.get('User-Agent', 'Unknown')}"
    )
    if wants_json_response():
        return jsonify({"error": e.description or "Not found"}), 404
    return render_template("error/404.html"), 404


def forbidden(e):
    from flask import current_app

    current_app.logger.warning(
        f"Forbidden access: {request.url} - User Agent: {request.headers.get('User-Agent', 'Unknown')}"
    )
    if wants_json_response():
        return jsonify({"error": e.description or "Forbidden"}), 403
    return render_template("error/403.html"), 403


def too_many_requests(e):
    """Custom error handler for rate limiting (429 errors)"""
    from flask import current_app

    current_app.logger.warning(
        f"Rate limit exceeded: {request.url} - User Agent: {request.headers.get('User-Agent', 'Unknown')}"
    )
    if wants_json_response():
        return jsonify({"error": e.description or "Too many requests"}), 429
    return render_template("error/429.html", error=e), 429


def internal_server_error(e):
    # Unlike the handlers above this one does not log: Flask's own log_exception
    # already wrote the traceback before calling us, and the single explicit
    # abort(500) logs at its call site. `e` is the InternalServerError wrapper —
    # the cause is e.original_exception.
    if wants_json_response():
        return jsonify({"error": "Internal server error"}), 500
    return render_template("error/500.html"), 500
