"""Regression test: autocomplete_ags must HTML-escape database values.

The /statistik/ags endpoint builds HTML in Python and returns it for HTMX
innerHTML swap. Without escaping, a tainted gen value would execute as XSS.
"""

from app.database.models import TblAemterCoordinaten


def test_autocomplete_escapes_html_in_gen(client, session):
    """Values containing HTML chars must be escaped in the response."""
    xss_gen = '<img src=x onerror=alert(1)>'
    row = TblAemterCoordinaten(
        ags=99999999,
        gen=xss_gen,
        properties={"test": True},
    )
    session.add(row)
    session.flush()

    response = client.get("/statistik/ags?ags_input=99999999")
    html = response.data.decode()

    # The raw XSS payload must NOT appear unescaped
    assert xss_gen not in html
    # Angle brackets must be escaped — this neutralizes the tag entirely
    assert "&lt;img" in html
    assert "&gt;" in html
