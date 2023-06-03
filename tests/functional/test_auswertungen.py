from app import create_app


def test_request_example(client):
    response = client.get("/auswertungen")
    text = bytes("Übersicht Fundmeldungen"
                 , 'utf-8')
    assert text in response.data

