import pytest
from unittest.mock import patch
from app.routes.statistics import stats_bardiagram_datum

@pytest.fixture
def custom_date_request(form_data_request):
    """Fixture für einen Request mit spezifischem Datumszeitraum für Fundatum-Tests."""
    form_data_request.form = {
        'dateFrom': '2024-01-07',
        'dateTo': '2024-03-06',
        'user_id': '9999'
    }
    return form_data_request

@pytest.mark.usefixtures("session_with_user", "request_context")
def test_stats_funddatum(custom_date_request, session):
    """Test dass die stats_bardiagram_datum Funktion korrekte Daten liefert
    für den Fundort-Datumsbereich."""

    with patch('app.routes.statistics.render_template') as mock_render_template:
        # Mock-Rückgabewert setzen
        mock_render_template.return_value = None

        # Funktion aufrufen
        stats_bardiagram_datum(
            request=custom_date_request,
            dbfields=['dat_fund_von'],
            page='stats-funddatum.html',
            marker='meldungen_funddatum',
            dateFrom='2024-01-07',
            dateTo='2024-03-06'
        )

        # Nur trace1 (Werte für die Grafik) prüfen
        mock_render_template.assert_called_once()
        actual_values = mock_render_template.call_args[1]['trace1']

        expected_values = {
            'x': ['2024-01-20', '2024-01-28', '2024-02-12', '2024-02-19'],
            'y': [1, 1, 1, 1]
        }

        assert actual_values == expected_values, \
            f"Expected values: {expected_values}, but got: {actual_values}"
