"""Tests for app/__init__.py CLI commands and error handlers."""
from unittest.mock import patch, MagicMock
from flask import Flask
from app import (
    page_not_found,
    forbidden,
    too_many_requests
)





def test_flask_app_with_testing_config():
    """Test the Flask app creation with testing configuration."""
    # Test an init parameter that we haven't hit yet
    from app import create_app
    from app.test_config import Config as TestConfig

    # Create app with explicit test config
    app = create_app(TestConfig)

    # Verify that the test config parameters are set
    assert app.config.get('TESTING') is True

    # Check that important application components are initialized
    assert hasattr(app, 'jinja_env'), "Jinja environment should be initialized"
    assert hasattr(app, 'url_map'), "URL map should be initialized"

    # Verify routes are registered
    rules = [rule.endpoint for rule in app.url_map.iter_rules()]
    assert 'static' in rules, "Static routes should be registered"

    # Verify context processor
    assert 'now' in app.jinja_env.globals or any(
        'now' in processor() for processor in app.template_context_processors[None]
    ), "Context processor for 'now' should be registered"


def test_error_handlers_register():
    """Test that error handlers are properly registered and work."""
    from app import create_app
    from app.test_config import Config as TestConfig
    app = create_app(TestConfig)
    
    # Test 404 handler
    with app.test_client() as client:
        response = client.get('/nonexistent-page-12345')
        assert response.status_code == 404  # Unknown routes return 404
        
    # Test that error handlers are actually registered
    assert 404 in app.error_handler_spec[None]
    assert 403 in app.error_handler_spec[None]
    assert 429 in app.error_handler_spec[None]

def test_error_handler_return_values(app):
    """Test the return values of error handler functions."""
    with app.test_request_context():
        # Test each handler directly
        response_404, status_404 = page_not_found(None)
        assert isinstance(response_404, str)
        assert status_404 == 404
        assert "404" in response_404 or "nicht gefunden" in response_404.lower()

        response_403, status_403 = forbidden(None)
        assert isinstance(response_403, str)
        assert status_403 == 403
        assert "403" in response_403 or "verboten" in response_403.lower()

        response_429, status_429 = too_many_requests(None)
        assert isinstance(response_429, str)
        assert status_429 == 429
        assert "429" in response_429 or "zu viele" in response_429.lower()

def test_context_processor():
    """Test that the context processor for inject_now is registered."""
    # Create a mock app with a context_processor method that we can track
    app = Flask('test_app')
    app.context_processor = MagicMock()

    # Create the app with our mock
    from app import create_app
    with patch('app.Flask', return_value=app):
        # Call create_app which should register the context processor
        create_app()

        # Verify context_processor was called at least once
        assert app.context_processor.called
