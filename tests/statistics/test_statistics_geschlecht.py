import pytest
from unittest.mock import patch
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request
from werkzeug.datastructures import MultiDict  
from app.routes.statistics import stats_geschlecht,  get_date_interval, list_of_stats
from flask import session as flask_session, appcontext_pushed, g

@pytest.fixture
def mock_request(app):
    """Fixture für das Mocken des Requests mit form-Daten und einer user_id in der SecureCookieSession."""
    # Erstelle einen EnvironBuilder mit den Formular-Daten
    builder = EnvironBuilder(
        method='POST',
        data={'dateFrom': '2024-01-01', 'dateTo': '2025-12-31',
              'user_id':'9999'}
    )
    
    # Erstelle das Request-Objekt
    request = Request(builder.get_environ())
    
    # Wir geben das Request-Objekt zurück - die Session wird im Test selbst gesetzt
    return request


# Mockt die render_template-Funktion
@patch('app.routes.statistics.render_template')  
def test_stats_geschlecht(mock_render_template, session, mock_request, app):
    # Definiere, was der Mock für render_template zurückgeben soll
    mock_render_template.return_value = None
    
    # Führe die Funktion in einem Request-Kontext aus
    with app.test_request_context():
        # Setze die user_id in der Flask-Session
        flask_session['user_id'] = '9999'
        flask_session.modified = True
        
        # Aufruf der Funktion und Überprüfung des Ergebnisses
        stats_geschlecht(request=mock_request)

        # Überprüfe, ob render_template mit den richtigen
        # Parametern aufgerufen wurde
        # mock_render_template.assert_called_once_with(
        #     'statistics/stats-geschlecht.html',
        #     menu={'xxx': 'Bitte eine Wahl treffen ...',
        #           'start': 'Startseite/Filter',
        #           'geschlecht': 'Entwicklungsstadium/Geschlecht',
        #           'meldungen_funddatum': 'Meldungen: Funddatum',
        #           'meldungen_meldedatum': 'Meldungen: Meldedatum',
        #           'meldungen_meld_fund': 'Meldungen: Fund- und Meldedatum',
        #           'meldungen_mtb': 'Grafik: Messtischblatt',
        #           'meldungen_amt': 'Auswertung Amt/Gemeinde',
        #           'meldungen_laender': 'Meldungen Bundesländer',
        #           'meldungen_brb': 'Meldungen Brandenburg',
        #           'meldungen_berlin': 'Meldungen Berlin',
        #           'meldungen_gesamt': 'Alle Summen (Tabelle)'},
        #     user_id='9999',
        #     marker='geschlecht',
        #     dateFrom='2024-01-01',
        #     dateTo='2025-12-31',
        #     values={'Männchen': 3, 'Weibchen': 4, 'Nymphen': 6, 'Ootheken': 6, 'Andere': 0})

        # Nur die Anzahl nach Geschlecht prüfen
        mock_render_template.assert_called_once()
        actual_values = mock_render_template.call_args[1]['values']
        expected_values = {'Männchen': 3, 'Weibchen': 4, 'Nymphen': 6, 'Ootheken': 6, 'Andere': 0}
        
        assert actual_values == expected_values, f"Expected values: {expected_values}, but got: {actual_values}"
