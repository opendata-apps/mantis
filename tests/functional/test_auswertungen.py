def test_request_example(client):
    response = client.get("/auswertungen")
    text = bytes("Fundmeldungen", "utf-8")
    assert text in response.data
