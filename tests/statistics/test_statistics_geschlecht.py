import pytest
from unittest.mock import patch
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request
from flask.sessions import SecureCookieSession
from werkzeug.datastructures import MultiDict  
#from your_module import stats_geschlecht  # Passe den Import an den tatsächlichen Pfad an
from app.routes.statistics import stats_geschlecht,  get_date_interval, list_of_stats
#from flask import render_template
# Testdaten
mock_result = [{'Männchen': 3, 'Weibchen': 4, 'Nymphen': 6, 'Ootheken': 6, 'Andere': 0}]

@pytest.fixture
def mock_request():
    """Fixture für das Mocken des Requests mit form-Daten und einer user_id in der SecureCookieSession."""
    # Erstelle einen EnvironBuilder mit den Formular-Daten
    builder = EnvironBuilder(
        method='POST',
        data={'dateFrom': '2024-01-01', 'dateTo': '2025-12-31'}
    )
    
    # Erstelle das Request-Objekt
    request = Request(builder.get_environ())
    
    # Erstelle und setze die Session als SecureCookieSession
    session = SecureCookieSession()
    session['user_id'] = '9999'  # Setze die user_id
    
    # Verknüpfe die Session mit dem Request
    request.session = session

    return request


# Mockt die render_template-Funktion
@patch('app.routes.statistics.render_template')  
def test_stats_geschlecht(mock_render_template, session, mock_request):
    # Definiere, was der Mock für render_template zurückgeben soll
    mock_render_template.return_value = None
    # Wir müssen nur die Übergabewerte überprüfen
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
    
    # Vergleiche die Werte
    assert actual_values == expected_values, f"Expected values: {expected_values}, but got: {actual_values}"
