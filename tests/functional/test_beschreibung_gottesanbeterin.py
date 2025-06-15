def test_mantis_description_page_contains_species_info(client):
    """Test that the mantis description page loads and contains species information."""
    response = client.get("/mantis-religiosa")
    assert response.status_code == 200
    assert "Die Europäische Gottesanbeterin".encode('utf-8') in response.data
