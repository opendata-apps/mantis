"""Server handling of originals uploaded when browser conversion fails.

When the client-side canvas pipeline cannot produce a WebP it now falls back to
posting the untouched camera file, so the server is the component that has to
orient it correctly and refuse a frame with no visible pixels (the Android
WebView blank-canvas bug that produced reports 10595, 16651, 17355, 21953,
23905, 26254 and 31196).
"""

from datetime import date

import pytest
from PIL import Image

from app.routes.report import BlankImageError, _process_uploaded_image
from tests.helpers import build_valid_report_form_data, make_test_image


@pytest.fixture(autouse=True)
def upload_folder(app, tmp_path, monkeypatch):
    """Every test here writes images; keep them out of the real datastore."""
    monkeypatch.setitem(app.config, "UPLOAD_FOLDER", str(tmp_path))
    return tmp_path


def _webp(alpha):
    """A lossless WebP whose every pixel has the given alpha."""
    return make_test_image(
        fmt="webp",
        name="sighting.webp",
        size=(64, 64),
        mode="RGBA",
        color=(0, 0, 0, alpha),
    )


def _store(photo):
    return _process_uploaded_image(photo, date(2025, 6, 1), "Testdorf", "9999")


def test_original_jpeg_is_stored_as_webp(upload_folder):
    rel = _store(make_test_image(size=(200, 100)))

    assert Image.open(upload_folder / rel).format == "WEBP"


@pytest.mark.parametrize(
    "orientation, expected",
    [(None, (200, 100)), (6, (100, 200))],
    ids=["upright-untouched", "orientation-6-rotated"],
)
def test_exif_orientation_is_baked_in(upload_folder, orientation, expected):
    """Orientation 6 means "rotate 90° CW to display".

    The browser applies this when drawing to a canvas, so the converted path was
    always upright. An original goes to Pillow untouched, and a WebP re-encode
    drops the EXIF tag — so without transposing, a portrait photo is archived
    sideways with nothing left to correct it. Canvas-produced files carry no
    EXIF at all, which is why the upright case must stay a no-op.
    """
    rel = _store(make_test_image(size=(200, 100), orientation=orientation))

    assert Image.open(upload_folder / rel).size == expected


def test_blank_image_is_refused(upload_folder):
    with pytest.raises(BlankImageError):
        _store(_webp(alpha=0))

    # A refused frame must not leave anything behind.
    assert list(upload_folder.rglob("*.webp")) == []
    assert list(upload_folder.rglob("*.part")) == []


def test_opaque_image_is_not_mistaken_for_blank(upload_folder):
    """A dark photo is not a blank one — only the alpha channel decides."""
    rel = _store(_webp(alpha=255))

    assert (upload_folder / rel).is_file()


def _submission(photo):
    return build_valid_report_form_data(photo=photo)


def test_submission_accepts_an_original_jpeg(client, upload_folder):
    """The fallback path end to end: an untouched camera file is a valid report."""
    resp = client.post(
        "/melden",
        data=_submission((make_test_image(size=(200, 100)), "IMG_1234.jpg")),
        content_type="multipart/form-data",
    )

    assert resp.status_code == 200, resp.get_data(as_text=True)[:500]
    assert resp.get_json()["success"] is True
    assert len(list(upload_folder.rglob("*.webp"))) == 1


def test_submission_rejects_a_blank_photo_with_a_field_error(client, upload_folder):
    """A blank frame is a photo problem, not a server error: say so, and keep
    the rest of the form so the reporter only has to re-pick the image."""
    resp = client.post(
        "/melden",
        data=_submission((_webp(alpha=0), "sighting.webp")),
        content_type="multipart/form-data",
    )

    assert resp.status_code == 400, resp.get_data(as_text=True)[:500]
    assert "photo" in resp.get_json()["errors"]
    assert list(upload_folder.rglob("*.webp")) == []
