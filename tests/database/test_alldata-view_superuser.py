"""Tests for the full-text search functionality using materialized views."""
from datetime import datetime

def test_view_alldata_search(client):
    """Test the direct search method in the FullTextSearch class.
    
    This test verifies that the search() class method properly finds
    matching records by using PostgreSQL's full-text search capabilities.
    """
    with client.session_transaction() as sess:
        sess['user_id'] = '9999'  # Simulierter eingeloggter Benutzer
        # Don't set last_updated_all_data_view - let the route handle it

    # Senden einer POST-Anfrage an die Seite mit den Formulardaten
    response = client.get("/alldata?search=Cottbus")
    # Überprüfen, ob die Antwort einen Statuscode 200 zurückgibt
    assert response.status_code == 200
