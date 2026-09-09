"""Atomicity of report image storage (finding #1: orphaned files).

Layer A: `_process_uploaded_image` publishes atomically (temp -> replace), so a
failure never leaves a partial/0-byte file at the final path.
Layer B: a submission that fails after the image is written removes the file,
so no orphan with a missing fundorte row is left behind.
"""

import io
from datetime import date
from pathlib import Path

import pytest
from PIL import Image

import app.routes.report as report_mod
from app.routes.report import _process_uploaded_image


pytestmark = pytest.mark.usefixtures("app_ctx")


def _webp_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), "green").save(buf, format="WEBP")
    return buf.getvalue()


def test_process_image_success_publishes_atomically(app, tmp_path, monkeypatch):
    monkeypatch.setitem(app.config, "UPLOAD_FOLDER", str(tmp_path))

    rel = _process_uploaded_image(
        io.BytesIO(_webp_bytes()), date(2025, 6, 1), "Testdorf", "9999"
    )

    assert (tmp_path / rel).is_file()
    # No temp artifact left behind anywhere under the upload root.
    assert list(tmp_path.rglob("*.part")) == []


def test_process_image_failure_leaves_no_partial_or_final(app, tmp_path, monkeypatch):
    monkeypatch.setitem(app.config, "UPLOAD_FOLDER", str(tmp_path))

    # Make the atomic publish fail *after* the temp file has been written.
    def boom(self, target):
        raise OSError("simulated rename failure")

    monkeypatch.setattr(Path, "replace", boom)

    with pytest.raises(OSError):
        _process_uploaded_image(
            io.BytesIO(_webp_bytes()), date(2025, 6, 1), "Testdorf", "9999"
        )

    assert list(tmp_path.rglob("*.webp")) == []
    assert list(tmp_path.rglob("*.part")) == []


def test_failed_submission_does_not_orphan_image(app, client, tmp_path, monkeypatch):
    """POST that fails after the image write must leave no file on disk."""
    monkeypatch.setitem(app.config, "UPLOAD_FOLDER", str(tmp_path))

    # Inject a failure at the spatial-enrichment step, which runs *after* the
    # image has been written to disk (report.py: _process_uploaded_image at the
    # photo step, calculate_spatial_fields immediately after).
    def boom(lat, lon):
        raise RuntimeError("simulated enrichment failure")

    monkeypatch.setattr(report_mod, "calculate_spatial_fields", boom)

    data = {
        "report_first_name": "Test",
        "report_last_name": "User",
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
