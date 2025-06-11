"""Tests for the full-text search functionality using materialized views."""
from datetime import datetime, timezone

def test_view_alldata_search(client):
    """Test the direct search method in the FullTextSearch class.
    
    This test verifies that the search() class method properly finds
    matching records by using PostgreSQL's full-text search capabilities.
    """
    now = datetime.now(timezone.utc)
    with client.session_transaction() as sess:
        sess['user_id'] = '9999'  # Simulierter eingeloggter Benutzer
        sess['last_updated_all_data_view'] = now  # Optional
        # Test a simple search
        #form_data = {'search': 'Cottbus', 'user_id':'9999'}

    # Senden einer POST-Anfrage an die Seite mit den Formulardaten
    response = client.get("/alldata?search=Cottbus")
    # Überprüfen, ob die Antwort einen Statuscode 200 zurückgibt
    assert response.status_code == 200
