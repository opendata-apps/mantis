import datetime
import io
import json

from bs4 import BeautifulSoup
from PIL import Image


def set_client_user(client, user_id: str):
    """Set the authenticated user ID in a Flask test client session."""
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
    return client


def clear_client_session(client):
    """Clear the Flask test client session."""
    with client.session_transaction() as sess:
        sess.clear()
    return client


def make_test_image(
    *,
    fmt: str = "jpeg",
    name: str = "test.jpg",
    size: tuple[int, int] = (10, 10),
    color: str = "green",
):
    """Create a small in-memory image for upload tests."""
    buf = io.BytesIO()
    Image.new("RGB", size, color=color).save(buf, fmt)
    buf.name = name
    buf.seek(0)
    return buf


def build_valid_report_form_data(*, sighting_days_ago: int = 3, **overrides):
    """Build a valid base payload for the report submission form."""
    sighting_date = (
        datetime.date.today() - datetime.timedelta(days=sighting_days_ago)
    ).strftime("%Y-%m-%d")
    data = {
        "report_first_name": "Anna",
        "report_last_name": "Testerin",
        "email": "anna@example.com",
        "identical_finder_reporter": "true",
        "finder_first_name": "",
        "finder_last_name": "",
        "feedback_source": "",
        "feedback_detail": "",
        "sighting_date": sighting_date,
        "latitude": "52.520008",
        "longitude": "13.404954",
        "fund_city": "Berlin",
        "fund_state": "Berlin",
        "fund_district": "Mitte",
        "fund_street": "Alexanderplatz 1",
        "fund_zip_code": "10178",
        "gender": "Männlich",
        "location_description": "2",
        "description": "Auf einer Pflanze entdeckt",
        "honeypot": "",
    }
    data.update(overrides)
    return data


def extract_reports_json(response_data):
    """Extract the inline `const reports = [...]` payload from the map page."""
    soup = BeautifulSoup(response_data, "html.parser")

    for script in soup.find_all("script"):
        if script.string and "const reports = " in script.string:
            start = script.string.find("const reports = ") + len("const reports = ")
            bracket_count = 0
            end = start
            for i, char in enumerate(script.string[start:], start):
                if char == "[":
                    bracket_count += 1
                elif char == "]":
                    bracket_count -= 1
                    if bracket_count == 0:
                        end = i + 1
                        break
            return json.loads(script.string[start:end])

    raise AssertionError("Could not find reports JSON in response")
