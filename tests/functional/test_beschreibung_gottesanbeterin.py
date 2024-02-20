from app import create_app


def test_request_example(client):
    response = client.get("/mantis-religiosa")
    text = bytes("Die faszinierende Welt der", "utf-8")
    assert text in response.data
