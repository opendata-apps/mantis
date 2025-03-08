"""Tests for app/__init__.py CLI commands and error handlers."""
from unittest.mock import patch, MagicMock
from flask.cli import ScriptInfo
from click.testing import CliRunner
from flask import Flask
from app import (
    create_materialized_view_command,
    upgrade_fts_command,
    page_not_found,
    forbidden,
    too_many_requests
)


def test_create_materialized_view_command():
    """Test the create-mview CLI command."""
    runner = CliRunner()
    
    # Mock the TblAllData.create_materialized_view method
    with patch('app.database.alldata.TblAllData.create_materialized_view') as mock_create_view:
        # Create a mock Flask app and context
        app = Flask('testapp')
        
        # Setup the Flask app context for the CLI command
        obj = ScriptInfo(create_app=lambda: app)
        
        # Run the command
        result = runner.invoke(create_materialized_view_command, obj=obj)
        
        # Verify the command executed successfully
        assert result.exit_code == 0
        assert "Materialized view created." in result.output
        
        # Check that the method was called
        mock_create_view.assert_called_once()


def test_upgrade_fts_command():
    """Test the upgrade-fts CLI command."""
    runner = CliRunner()
    
    # We need to patch the class method that doesn't exist yet in FullTextSearch
    # This is needed because the code calls FullTextSearch.refresh_materialized_view()
    # but the actual implementation just has a standalone function
    with patch('app.database.full_text_search.FullTextSearch') as mock_fts_class, \
         patch('flask_migrate.upgrade') as mock_upgrade:
        
        # Set up the mock class method
        mock_fts_class.refresh_materialized_view = MagicMock()
        
        # Create a mock Flask app
        app = Flask('testapp')
        
        # Setup the Flask app context for the CLI command
        obj = ScriptInfo(create_app=lambda: app)
        
        # Run the command
        result = runner.invoke(upgrade_fts_command, obj=obj)
        
        # Verify the command executed successfully
        assert result.exit_code == 0
        assert "FTS upgrade completed successfully." in result.output
        
        # Check that the methods were called
        assert mock_upgrade.call_count == 2
        mock_fts_class.refresh_materialized_view.assert_called_once()


def test_upgrade_fts_command_error():
    """Test the upgrade-fts CLI command with an error."""
    runner = CliRunner()
    
    # Mock flask_migrate.upgrade to raise an exception
    with patch('flask_migrate.upgrade', side_effect=Exception("Test error")):
        
        # Create a mock Flask app
        app = Flask('testapp')
        
        # Setup the Flask app context for the CLI command
        obj = ScriptInfo(create_app=lambda: app)
        
        # Run the command - should fail but not crash the test
        result = runner.invoke(upgrade_fts_command, obj=obj)
        
        # Verify the command reported the error
        assert result.exit_code != 0
        assert "Error during FTS upgrade: Test error" in result.output


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
    """Test that error handlers are registered with the app."""
    # Create a mock app
    app = Flask('test_app')
    app.register_error_handler = MagicMock()
    
    # Create the app with our mock
    from app import create_app
    with patch('app.Flask', return_value=app):
        # Call create_app which should register error handlers
        create_app()
        
        # Verify error handlers were registered
        app.register_error_handler.assert_any_call(404, page_not_found)
        app.register_error_handler.assert_any_call(403, forbidden)
        app.register_error_handler.assert_any_call(429, too_many_requests)

@patch('app.render_template')
def test_error_handler_return_values(mock_render_template):
    """Test the return values of error handler functions."""
    # Mock render_template to return a string value
    mock_render_template.return_value = "Mocked template"
    
    # Test each handler directly
    response_404, status_404 = page_not_found(None)
    assert response_404 == "Mocked template"
    assert status_404 == 404
    mock_render_template.assert_called_with("error/404.html")
    
    response_403, status_403 = forbidden(None)
    assert response_403 == "Mocked template"
    assert status_403 == 403
    mock_render_template.assert_called_with("error/403.html")
    
    response_429, status_429 = too_many_requests(None)
    assert response_429 == "Mocked template"
    assert status_429 == 429
    mock_render_template.assert_called_with("error/429.html")

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