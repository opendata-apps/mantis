"""Tests for the alldata materialized view search."""


def test_view_alldata_search(client):
    """Test the alldata view search endpoint.

    This test verifies that the alldata view search API endpoint
    returns data successfully for authenticated users.
    """
    with client.session_transaction() as sess:
        sess["user_id"] = "9999"  # Simulierter eingeloggter Benutzer
        # Don't set last_updated_all_data_view - let the route handle it

    # Senden einer POST-Anfrage an die Seite mit den Formulardaten
    response = client.get("/alldata?search=Cottbus")
    # Überprüfen, ob die Antwort einen Statuscode 200 zurückgibt
    assert response.status_code == 200
