import os
import tomllib
from datetime import datetime
from pathlib import Path

import pillow_heif
from flask import (
    Flask,
    current_app,
    jsonify,
    render_template,
    request,
    session,
    url_for,
)
from flask_limiter.errors import RateLimitExceeded
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config
from .extensions import (
    csrf,
    db,
    flask_favicon,
    limiter,
    login_manager,
    mail,
    migrate,
)

with (Path(__file__).resolve().parent.parent / "pyproject.toml").open(
    "rb"
) as _pyproject:
    __version__ = tomllib.load(_pyproject)["project"]["version"]


def create_app(config_class=Config) -> Flask:
    # The bare package: Flask names its logger after it, and only an "app"
    # logger passes its level and handler to app/tools' getLogger(__name__).
    app = Flask(__name__.split(".")[0])
    app.config.from_object(config_class)

    configure_logger(app)
    # Adds HEIC/HEIF to Image.open for iPhone uploads.
    pillow_heif.register_heif_opener()
    register_extensions(app)
    # Flask re-signs only a permanent session per request, so this makes
    # PERMANENT_SESSION_LIFETIME an idle limit for every visitor.
    app.before_request(_make_session_permanent)
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


def _make_session_permanent() -> None:
    session.permanent = True


def register_extensions(app: Flask) -> None:
    # login_manager's callbacks live in app.auth; the blueprints import it.
    csrf.init_app(app)
    db.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    flask_favicon.init_app(app)
    login_manager.init_app(app)

    flask_favicon.register_favicon("app/static/images/logo.png", "default")

    migrate.init_app(app, db)

    from app.tools import vite

    vite.init_app(app)


def register_template_globals(app: Flask) -> None:
    # Heroicons — usage: {{ heroicon_outline("map-pin", class="w-4 h-4") }}
    from heroicons.jinja import heroicon_mini, heroicon_outline

    from app.tools.coordinate_validation import COORDINATE_RANGES
    from app.tools.image_upload import upload_config

    def url_for_page(endpoint: str, page: int) -> str:
        """Another page of the current listing, carrying every active filter.

        Flask's own underscore arguments are dropped: a crafted ?_scheme= would
        otherwise reach url_for and raise while the page renders.
        """
        args = {
            key: value for key, value in request.args.items() if not key.startswith("_")
        }
        args["page"] = str(page)
        return url_for(endpoint, **args)  # ty: ignore[invalid-argument-type]

    app.jinja_env.globals.update(
        {
            "coord_range": COORDINATE_RANGES,
            "heroicon_mini": heroicon_mini,
            "heroicon_outline": heroicon_outline,
            "upload_config": upload_config(),
            "url_for_page": url_for_page,
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
        request.environ["mantis.route"] = str(request.url_rule or "unmatched")
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Keep the site origin for map-provider attribution, never private paths.
        response.headers["Referrer-Policy"] = "strict-origin"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        # Explicitly off, not absent: OWASP Secure Headers asks for "0" so a
        # legacy browser cannot fall back to its own buggy XSS auditor.
        response.headers["X-XSS-Protection"] = "0"
        if app.config.get("PREFERRED_URL_SCHEME") == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        # No 'unsafe-eval': every JS entrypoint sets htmx.config.allowEval = false.
        # 'unsafe-inline' serves the inline handlers and <script> blocks (TODO:
        # move them to listeners). 'wasm-unsafe-eval' lets heic2any compile;
        # blob: workers are canvas-confetti's renderer.
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

    # htmx 2 swaps nothing on a 4xx, so an auth or CSRF denial would fail
    # silently; HX-Redirect turns it into a full-page navigation.
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
    current_app.logger.warning(
        "Page not found: route=%s", request.url_rule or "unmatched"
    )
    if wants_json_response():
        return jsonify({"error": e.description or "Not found"}), 404
    return render_template("error/404.html"), 404


def forbidden(e):
    current_app.logger.warning(
        "Forbidden access: route=%s", request.url_rule or "unmatched"
    )
    if wants_json_response():
        return jsonify({"error": e.description or "Forbidden"}), 403
    return render_template("error/403.html"), 403


def too_many_requests(e):
    """Custom error handler for rate limiting (429 errors)"""
    current_app.logger.warning(
        "Rate limit exceeded: route=%s", request.url_rule or "unmatched"
    )
    if wants_json_response():
        # flask-limiter's description is "3 per 1 minute", and the report form
        # shows the error text to the reporter as is.
        if isinstance(e, RateLimitExceeded):
            message = (
                "Zu viele Anfragen in kurzer Zeit. Bitte warten Sie eine "
                "Minute und versuchen Sie es dann erneut."
            )
        else:
            message = e.description or "Too many requests"
        return jsonify({"error": message}), 429
    return render_template("error/429.html", error=e), 429


def internal_server_error(e):
    # Not logged here: Flask's log_exception already wrote the traceback.
    if wants_json_response():
        return jsonify({"error": "Internal server error"}), 500
    return render_template("error/500.html"), 500
