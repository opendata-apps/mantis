from app import create_app
import os


def test_home_page():
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid
    """
    # Set the Testing configuration prior to creating the Flask application
    os.environ["CONFIG_TYPE"] = "config.TestingConfig"
    flask_app = create_app()

    # Create a test client using the Flask application configured for testing
    with flask_app.test_client() as test_client:
        response = test_client.get("/")
        assert response.status_code == 200
        assert b"Gottesanbeterin gesucht" in response.data
        header1 = bytes("Über das Projekt", "utf-8")
        assert header1 in response.data
        header2 = bytes("ÜBER <i>Mantis religiosa</i> L. 1758", "utf-8")
        assert header2 in response.data
        assert b"Was passiert mit meiner Meldung?" in response.data
