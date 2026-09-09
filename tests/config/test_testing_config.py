"""The running test app preserves production settings except explicit overrides."""

from http.cookies import SimpleCookie

from app.config import Config as AppConfig


def _settings(config):
    return {name for name in dir(config) if name.isupper()}


def test_no_production_setting_is_invisible_to_tests(app):
    missing = _settings(AppConfig) - app.config.keys()
    assert not missing, (
        f"These production settings would not apply in tests: {sorted(missing)}. "
        "The application factory must load the inherited settings."
    )


def test_overrides_are_deliberate(app):
    """Every difference from production is one of the documented exceptions."""
    expected = {
        "BACKUPMAIL",
        "BACKUP_DIR",
        "DATABASE_DB",
        "FAVICON_BUILD_DIR",
        "MIN_MAP_YEAR",
        "PHOTO_SUPPORT_EMAIL",
        "REMEMBER_COOKIE_SECURE",
        "REVIEWERMAIL",
        "SECRET_KEY",
        "SESSION_COOKIE_SECURE",
        "SQLALCHEMY_DATABASE_URI",
        "TESTING",
        "UPLOAD_FOLDER",
        "WTF_CSRF_ENABLED",
    }
    differing = {
        name
        for name in _settings(AppConfig) & app.config.keys()
        if getattr(AppConfig, name) != app.config[name]
    }
    # Subset, not equality: the env-dependent ones only differ on a machine
    # whose .env differs. An unlisted override is the failure worth catching.
    assert differing <= expected, (
        f"undocumented overrides: {sorted(differing - expected)}"
    )


def test_reviewer_login_applies_cookie_protection(app, client):
    response = client.get("/reviewer/9999")
    assert response.status_code == 302
    cookies = SimpleCookie()
    for header in response.headers.getlist("Set-Cookie"):
        cookies.load(header)
    cookie = cookies[app.config["SESSION_COOKIE_NAME"]]
    flags = cookie["httponly"], cookie["samesite"]
    assert flags == (True, "Lax")


def test_debug_is_off_whatever_the_developer_env_says(app):
    """The diffs above cannot see this one: DEBUG never passes through a config.

    load_dotenv() puts FLASK_DEBUG into os.environ and Flask reads it in
    Flask.__init__, so only an explicit TestConfig.DEBUG overrides it. Left on,
    the factory skips ProxyFix and the logging setup and the suite covers
    different code than production runs.
    """
    assert app.debug is False
