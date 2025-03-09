def test_request_example(client):
    response = client.get("/mantis-religiosa")
    text = bytes("Die Europäische Gottesanbeterin", "utf-8")
    assert text in response.data
