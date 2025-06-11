import pytest
from unittest.mock import patch
from app.routes.statistics import stats_geschlecht


@pytest.mark.usefixtures("session_with_user", "request_context")
def test_stats_geschlecht(form_with_dates, session):
    """Test zur Prüfung der Statistik nach Geschlecht/Entwicklungsstadien."""

    with patch('app.routes.statistics.render_template') as mock_render_template:
        # Mock-Rückgabewert setzen
        mock_render_template.return_value = None

        # Funktion aufrufen
        stats_geschlecht(request=form_with_dates)

        # Überprüfe, ob render_template aufgerufen wurde
        mock_render_template.assert_called_once()

        # Nur die Anzahl nach Geschlecht prüfen
        actual_values = mock_render_template.call_args[1]['values']
        expected_values = {
            'Männchen': 3,
            'Weibchen': 4,
            'Nymphen': 6,
            'Ootheken': 6,
            'Andere': 0
        }

        assert actual_values == expected_values, \
            f"Expected values: {expected_values}, but got: {actual_values}"
