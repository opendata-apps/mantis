import pytest


def test_region_page_returns_200_for_valid_slug(client):
    """Regional page for a known slug returns 200."""
    response = client.get("/gottesanbeterin-in-deutschland/")
    assert response.status_code == 200


def test_region_page_returns_404_for_unknown_slug(client):
    """Regional page for unknown slug returns 404."""
    response = client.get("/gottesanbeterin-in-atlantis/")
    assert response.status_code == 404


def test_region_page_contains_title(client):
    """Regional page contains the page title from YAML."""
    response = client.get("/gottesanbeterin-in-deutschland/")
    assert b"Gottesanbeterin in Deutschland" in response.data


def test_region_page_contains_meta_description(client):
    """Regional page has a meta description."""
    response = client.get("/gottesanbeterin-in-brandenburg/")
    assert b'<meta name="description"' in response.data
    assert b"Brandenburg" in response.data


def test_region_page_contains_breadcrumbs(client):
    """Regional page contains breadcrumb navigation."""
    response = client.get("/gottesanbeterin-in-brandenburg/")
    assert b"BreadcrumbList" in response.data


def test_region_page_contains_cta(client):
    """Regional page contains call-to-action to report form."""
    response = client.get("/gottesanbeterin-in-berlin/")
    assert b"/melden" in response.data


def test_region_page_contains_canonical(client):
    """Regional page has a canonical URL."""
    response = client.get("/gottesanbeterin-in-deutschland/")
    assert b"canonical" in response.data
    assert b"gottesanbeterin-in-deutschland" in response.data


def test_region_page_contains_sections(client):
    """Regional page renders content sections."""
    response = client.get("/gottesanbeterin-in-deutschland/")
    assert b"Verbreitung" in response.data


def test_region_page_contains_sibling_links(client):
    """Brandenburg page links to Berlin (sibling)."""
    response = client.get("/gottesanbeterin-in-brandenburg/")
    assert b"gottesanbeterin-in-berlin" in response.data


def test_region_page_trailing_slash_redirect(client):
    """URL without trailing slash redirects to URL with slash."""
    response = client.get("/gottesanbeterin-in-deutschland")
    assert response.status_code in (301, 308)


def test_mantis_page_links_to_regional_pages(client):
    """Mantis religiosa page contains links to regional pages."""
    response = client.get("/mantis-religiosa")
    assert b"gottesanbeterin-in-brandenburg" in response.data
