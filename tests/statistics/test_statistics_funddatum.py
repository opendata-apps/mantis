import pytest
from unittest.mock import patch
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request
from app.routes.statistics import stats_bardiagram_datum
from flask import session as flask_session
from app import create_app
from app.test_config import Config as TestConfig


@pytest.fixture
def mock_request(app):
    """Fixture für das Mocken des Requests mit
    form-Daten und einer user_id in der Session."""
    # Create a test client and request context
    with app.test_request_context():
        # Set the session data
        flask_session['user_id'] = '9999'
        
        # Create environment with form data
        builder = EnvironBuilder(
            method='POST',
            data={'user_id': '9999'}
        )
        
        # Create the request object
        request = Request(builder.get_environ())
        
        # Make sure the request has access to the session
        request.environ['flask.session'] = flask_session
        
        yield request


# Mockt die render_template-Funktion
@patch('app.routes.statistics.render_template')
def test_stats_funddatum(mock_render_template, session, mock_request, app):
    # Use app context for the test
    with app.test_request_context():
        # Ensure session is available
        flask_session['user_id'] = '9999'
        
        # Definiere, was der Mock für render_template zurückgeben soll
        mock_render_template.return_value = None
        stats_bardiagram_datum(request=mock_request,
                           dbfields=['dat_fund_von'],
                           page='stats-funddatum.html',
                           marker='meldungen_funddatum',
                           dateFrom='2024-01-07',
                           dateTo='2024-03-06')

        # Nur trace1 (Werte für die Grafik) prüfen
        mock_render_template.assert_called_once()
        actual_values = mock_render_template.call_args[1]['trace1']

        expected_values = {'x': ['2024-01-20', '2024-01-28',
                             '2024-02-12', '2024-02-19'],
                       'y': [1, 1, 1, 1]}

        assert actual_values == expected_values, \
            f"Expected values: {expected_values}, but got: {actual_values}"
