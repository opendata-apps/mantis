"""The testing config must not silently drop production settings.

A setting missing from it is not a failure — the tests just stop covering it.
"""

from app import create_app
from app.config import Config as AppConfig
from tests.test_config import Config as TestConfig


def _settings(config):
    return {name for name in dir(config) if name.isupper()}


def test_no_production_setting_is_invisible_to_tests():
    missing = _settings(AppConfig) - _settings(TestConfig)
    assert not missing, (
        f"These production settings would not apply in tests: {sorted(missing)}. "
        "Testing config must inherit app.config.Config."
    )


def test_overrides_are_deliberate():
    """Every difference from production is one of the documented exceptions."""
    expected = {
        "BACKUPMAIL",
        "DATABASE_DB",
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
        for name in _settings(AppConfig) & _settings(TestConfig)
        if getattr(AppConfig, name) != getattr(TestConfig, name)
    }
    # Subset, not equality: the env-dependent ones only differ on a machine
    # whose .env differs. An unlisted override is the failure worth catching.
    assert differing <= expected, (
        f"undocumented overrides: {sorted(differing - expected)}"
    )


def test_debug_is_off_whatever_the_developer_env_says():
    """The diffs above cannot see this one: DEBUG never passes through a config.

    load_dotenv() puts FLASK_DEBUG into os.environ and Flask reads it in
    Flask.__init__, so only an explicit TestConfig.DEBUG overrides it. Left on,
    the factory skips ProxyFix and the logging setup and the suite covers
    different code than production runs.
    """
    assert create_app(TestConfig).debug is False
