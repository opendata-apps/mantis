import pytest

def test_request_example(client):
    response = client.get("/")
    assert b"Mitmachprojekt" in response.data


def test_request_weitere_infos(client):
    response = client.get("/")
    assert b"Gottesanbeterin gesucht!" in response.data


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
