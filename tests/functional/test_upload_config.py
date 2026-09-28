"""The photo rules reach the page exactly as Python defines them.

Six places used to spell out which formats are allowed and how large a photo
may be. They are now derived from app/tools/image_upload.py; these tests are
what keeps the rendered page from drifting away from it again, and they are
what tests/js/image-checks.test.js points at for the browser half.
"""

import json

from bs4 import BeautifulSoup

from app.forms import MantisSightingForm
from app.tools.image_upload import (
    IMAGE_TYPES,
    MAX_UPLOAD_BYTES,
    accept_attribute,
    display_formats,
    extension_by_mime,
    max_upload_mb,
)


def _form_page(client):
    response = client.get("/melden")
    assert response.status_code == 200
    return BeautifulSoup(response.get_data(as_text=True), "html.parser")


def test_json_block_carries_the_python_rules(client):
    """The browser reads this block instead of keeping its own tables."""
    block = _form_page(client).find("script", id="upload-config")
    assert block is not None, "render_photo_upload must emit #upload-config"
    assert block.get("type") == "application/json", (
        "a data block, not an executable script — otherwise CSP has to allow it"
    )

    config = json.loads(block.string)
    assert config["types"] == IMAGE_TYPES
    assert config["maxBytes"] == MAX_UPLOAD_BYTES
    assert config["maxMb"] == max_upload_mb()


def test_shared_mime_resolves_to_the_first_extension(client):
    """Serialising sorts the keys, so the reverse map cannot be built in JS.

    Sorted, "jpeg" precedes "jpg"; a browser inverting types itself would save
    a camera JPEG as .jpeg. The server derives extensionByMime instead.
    """
    block = _form_page(client).find("script", id="upload-config")
    config = json.loads(block.string)

    assert config["extensionByMime"] == extension_by_mime()
    assert config["extensionByMime"]["image/jpeg"] == "jpg"
    # The premise of the test: the transport really does reorder the map.
    assert list(config["types"]) == sorted(IMAGE_TYPES)


def test_file_input_accepts_exactly_the_allowed_types(client):
    photo_input = _form_page(client).find("input", {"type": "file", "id": "photo"})
    assert photo_input is not None

    accept = photo_input["accept"]
    assert accept == accept_attribute()
    # MIME types lead, or Android pickers grey out the whole gallery.
    assert accept.startswith("image/")
    for extension, mime in IMAGE_TYPES.items():
        assert mime in accept
        assert f".{extension}" in accept


def test_hint_text_names_the_formats_and_the_limit(client):
    text = _form_page(client).get_text()
    for label in display_formats():
        assert label in text
    assert f"{max_upload_mb()}MB" in text


def test_form_validator_uses_the_same_source(app_ctx):
    """FileAllowed and the rendered page cannot disagree about a format."""
    allowed = next(
        validator
        for validator in MantisSightingForm().photo.validators
        if hasattr(validator, "upload_set")
    )
    assert set(allowed.upload_set) == set(IMAGE_TYPES)


def test_jpeg_shares_a_mime_without_adding_a_format():
    """jpg and jpeg are two extensions but one format in the hint text."""
    assert IMAGE_TYPES["jpg"] == IMAGE_TYPES["jpeg"]
    assert display_formats().count("JPG") == 1
    assert "JPEG" not in display_formats()
