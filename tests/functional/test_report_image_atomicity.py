"""Atomicity of report image storage (finding #1: orphaned files).

Layer A: `process_uploaded_image` publishes atomically (temp -> replace), so a
failure never leaves a partial/0-byte file at the final path.
Layer B: a submission that fails after the image is written removes the file,
so no orphan with a missing fundorte row is left behind.
"""

import io
from datetime import date, datetime
from pathlib import Path

import pytest
from flask import Flask
from PIL import Image

import app.routes.report as report_mod
import app.tools.report_images as report_images
from app.tools.report_images import process_uploaded_image
from tests.helpers import build_valid_report_form_data, make_test_image


def _webp_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), "green").save(buf, format="WEBP")
    return buf.getvalue()


@pytest.mark.usefixtures("app_ctx")
def test_process_image_success_publishes_atomically(app, tmp_path, monkeypatch):
    monkeypatch.setitem(app.config, "UPLOAD_FOLDER", str(tmp_path))

    rel = process_uploaded_image(
        io.BytesIO(_webp_bytes()), date(2025, 6, 1), "Testdorf", "9999"
    )

    assert (tmp_path / rel).is_file()
    # No temp artifact left behind anywhere under the upload root.
    assert list(tmp_path.rglob("*.part")) == []


def test_uploads_at_the_same_time_keep_both_photos(tmp_path, monkeypatch):
    class FixedTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 9, 30, 12, 0, 0)

    monkeypatch.setattr(report_images, "datetime", FixedTime)
    first = make_test_image(fmt="webp", color="red").getvalue()
    second = make_test_image(fmt="webp", color="blue").getvalue()
    app = Flask(__name__)
    app.config["UPLOAD_FOLDER"] = str(tmp_path)

    with app.app_context():
        first_path = process_uploaded_image(
            io.BytesIO(first), date(2025, 6, 1), "Testdorf", "9999"
        )
        second_path = process_uploaded_image(
            io.BytesIO(second), date(2025, 6, 1), "Testdorf", "9999"
        )

    assert first_path != second_path
    assert (tmp_path / first_path).read_bytes() == first
    assert (tmp_path / second_path).read_bytes() == second


def test_decoder_lock_failure_is_a_server_error(app, client):
    root = Path(app.config["UPLOAD_FOLDER"])
    (root / ".image-decode.lock").mkdir(parents=True)
    response = client.post(
        "/melden",
        data=build_valid_report_form_data(
            photo=(make_test_image(fmt="webp"), "sighting.webp")
        ),
        content_type="multipart/form-data",
    )

    assert response.status_code == 500
    assert list(root.rglob("*.webp")) == []


def test_unicode_city_names_fit_the_stored_photo_path(client):
    response = client.post(
        "/melden",
        data=build_valid_report_form_data(
            fund_city="ﬃ" * 50,
            photo=(make_test_image(fmt="webp"), "sighting.webp"),
        ),
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert response.get_json()["success"] is True


@pytest.mark.usefixtures("app_ctx")
def test_process_image_failure_leaves_no_partial_or_final(app, tmp_path, monkeypatch):
    monkeypatch.setitem(app.config, "UPLOAD_FOLDER", str(tmp_path))

    # Make the atomic publish fail *after* the temp file has been written.
    def boom(self, target):
        raise OSError("simulated rename failure")

    monkeypatch.setattr(Path, "replace", boom)

    with pytest.raises(OSError, match="simulated rename failure"):
        process_uploaded_image(
            io.BytesIO(_webp_bytes()), date(2025, 6, 1), "Testdorf", "9999"
        )

    assert list(tmp_path.rglob("*.webp")) == []
    assert list(tmp_path.rglob("*.part")) == []


def test_failed_submission_does_not_orphan_image(app, client, tmp_path, monkeypatch):
    """POST that fails after the image write must leave no file on disk."""
    monkeypatch.setitem(app.config, "UPLOAD_FOLDER", str(tmp_path))

    # Inject a failure at the spatial-enrichment step, which runs *after* the
    # image has been written to disk (report.py: process_uploaded_image at the
    # photo step, calculate_spatial_fields immediately after).
    def boom(lat, lon):
        raise RuntimeError("simulated enrichment failure")

    monkeypatch.setattr(report_mod, "calculate_spatial_fields", boom)

    data = {
        "report_name": "Test User",
        "email": "",
        "sighting_date": "2025-06-01",
        "latitude": "52.4",
        "longitude": "13.0",
        "fund_city": "Testdorf",
        "fund_state": "Brandenburg",
        "gender": "Männlich",
        "location_description": "2",
        "identical_finder_reporter": "y",
        "honeypot": "",
        "photo": (io.BytesIO(_webp_bytes()), "sighting.webp"),
    }
    resp = client.post("/melden", data=data, content_type="multipart/form-data")

    assert resp.status_code == 500, resp.get_data(as_text=True)[:500]
    # The image that was written during the failed request must be gone.
    assert list(tmp_path.rglob("*.webp")) == []
    assert list(tmp_path.rglob("*.part")) == []


def test_a_failure_after_the_commit_keeps_the_saved_reports_photo(
    app, client, tmp_path, monkeypatch, session
):
    from flask_login import user_logged_in
    from sqlalchemy import select

    from app.database.models import TblFundorte

    monkeypatch.setitem(app.config, "UPLOAD_FOLDER", str(tmp_path))
    monkeypatch.setitem(app.config, "PROPAGATE_EXCEPTIONS", False)

    # The report is committed; logging the reporter in fails afterwards.
    def refuse_login(sender, user):
        raise RuntimeError("simulated login failure")

    data = build_valid_report_form_data(
        fund_city="Nachher", photo=(io.BytesIO(_webp_bytes()), "sighting.webp")
    )
    with user_logged_in.connected_to(refuse_login, app):
        client.post("/melden", data=data, content_type="multipart/form-data")

    ablage = session.scalar(
        select(TblFundorte.ablage).where(TblFundorte.ort == "Nachher")
    )
    assert ablage
    assert (tmp_path / ablage).is_file()
