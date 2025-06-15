import pytest


def test_home_page_contains_project_title(client):
    """Test that home page contains the project title."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Mitmachprojekt" in response.data


def test_home_page_contains_mantis_heading(client):
    """Test that home page contains the main heading."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Gottesanbeterin gesucht!" in response.data


def test_home_page_contains_scientific_name(client):
    """Test that home page contains the scientific name in italic."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"<i>Mantis religiosa</i> L. 1758" in response.data


@pytest.mark.parametrize("route,expected_content,status_code", [
    ('/', b"Mitmachprojekt", 200),
    ('/', b"Gottesanbeterin gesucht", 200),
    ('/mantis_religiosa', b"Mantis religiosa", 403),  # Seite erfordert Authentifizierung
    ('/nonexistentpage', None, 403)  # In dieser App führen unbekannte Routen zu 403
])
def test_routes_content_and_status(client, route, expected_content, status_code):
    """Test verschiedene Routen mit erwarteten Inhalten und Status-Codes."""
    response = client.get(route)
    assert response.status_code == status_code

    if expected_content is not None and status_code == 200:
        assert expected_content in response.data
