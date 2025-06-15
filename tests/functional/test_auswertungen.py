def test_statistics_page_loads_and_contains_reports_heading(client):
    """Test that the statistics page loads successfully and contains expected content."""
    response = client.get("/auswertungen")
    assert response.status_code == 200
    assert b"Fundmeldungen" in response.data
