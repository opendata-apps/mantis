import pytest
from unittest.mock import patch
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request
from app.routes.statistics import stats_bardiagram_datum
from flask import session


@pytest.fixture
def mock_request():
    """Fixture für das Mocken des Requests mit
    form-Daten und einer user_id in der Session."""
    # EnvironBuilder -- Formular-Daten
    builder = EnvironBuilder(
        method='POST',
        data={'user_id': '9999'}
    )

    # Erstelle das Request-Objekt
    request = Request(builder.get_environ())

    # Erstelle und setze die Session
    session['user_id'] = '9999'
    # Verknüpfe die Session mit dem Request
    request.session = session

    return request


# Mockt die render_template-Funktion
@patch('app.routes.statistics.render_template')
def test_stats_funddatum(mock_render_template, session, mock_request):
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
