from app import create_app


def test_request_example(client):
    response = client.get("/mantis-religiosa")
    text = bytes("Die Europäische Gottesanbeterin (Mantis religiosa L, 1758)"
                 , 'utf-8')
    assert text in response.data

