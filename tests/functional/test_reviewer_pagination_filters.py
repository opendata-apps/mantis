"""Pagination links have to carry every filter the reviewer set.

render_pagination used to name each filter as a macro argument. typeInput and
search_type were never added, so paging away from page 1 silently widened the
result set back to every species and reset the search mode to full text.
"""

from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup


def _page_links(response):
    soup = BeautifulSoup(response.get_data(as_text=True), "html.parser")
    hrefs = [str(a["href"]) for a in soup.find_all("a", href=True)]
    return [parse_qs(urlparse(h).query) for h in hrefs if "page=" in h]


def test_pagination_keeps_every_active_filter(client):
    with client.session_transaction() as session:
        session["_user_id"] = "9999"

    response = client.get(
        "/reviewer?statusInput=alle&typeInput=weiblich&search_type=id"
        "&dateType=meld&sort_order=id_desc&per_page=1"
    )
    assert response.status_code == 200

    links = _page_links(response)
    assert links, "no pagination links rendered — per_page=1 should produce several"
    for query in links:
        assert query.get("typeInput") == ["weiblich"]
        assert query.get("search_type") == ["id"]
        assert query.get("statusInput") == ["alle"]
        assert query.get("dateType") == ["meld"]
        assert query.get("sort_order") == ["id_desc"]


def test_pagination_targets_the_requested_page(client):
    with client.session_transaction() as session:
        session["_user_id"] = "9999"

    response = client.get("/reviewer?statusInput=alle&per_page=1&page=2")

    pages = {q["page"][0] for q in _page_links(response) if "page" in q}
    assert "1" in pages
    assert "3" in pages
    assert "2" not in pages, "the current page is rendered as text, not as a link"
