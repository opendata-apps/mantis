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
        
        # Check that we have the expected keys and that values are non-negative
        expected_keys = {'Männchen', 'Weibchen', 'Nymphen', 'Ootheken', 'Andere'}
        assert set(actual_values.keys()) == expected_keys, \
            f"Expected keys: {expected_keys}, but got: {set(actual_values.keys())}"
        
        # Check that all values are non-negative integers
        for key, value in actual_values.items():
            assert isinstance(value, int) and value >= 0, \
                f"Value for {key} should be a non-negative integer, but got: {value}"
        
        # Check that at least some data exists (not all zeros)
        assert sum(actual_values.values()) > 0, \
            "Should have at least some sightings in the test data"
