from app import create_app


def test_request_example(client):
    response = client.get("/")
    assert b"Mantis Projekt" in response.data

def test_request_weitere_infos(client):
    response = client.get("/")
    assert b"<u>Weitere Infos</u>" in response.data

