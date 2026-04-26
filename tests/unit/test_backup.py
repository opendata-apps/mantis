import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest
from flask import Flask
from werkzeug.exceptions import Forbidden

from app import mail
from app.routes import backup as backup_routes
from app.tools.send_backup_email import render_backup_email, send_backup_email


@pytest.fixture
def backup_app(tmp_path):
    app = Flask(__name__)
    app.config.update(
        BACKUP_DIR=str(tmp_path / "backups"),
        BACKUP_DOWNLOAD_MAX_AGE_SECONDS=604800,
        DATABASE_DB="mantis_tester",
        DATABASE_HOST="localhost",
        DATABASE_PASSWORD="mantis",
        DATABASE_PORT="5432",
        DATABASE_USER="mantis_user",
        MAIL_DEFAULT_SENDER="sender@example.com",
        MAIL_SUPPRESS_SEND=True,
        SECRET_KEY="backup-test-secret",
        TESTING=True,
        UPLOAD_FOLDER=str(tmp_path / "uploads"),
    )
    mail.init_app(app)
    with app.app_context():
        yield app


def test_render_backup_email_contains_download_url():
    text = render_backup_email("https://example.test/download", 7)

    assert "https://example.test/download" in text
    assert "7 Tage" in text
    assert "Datensicherung" in text


def test_send_backup_email_sends_message(backup_app):
    with mail.record_messages() as outbox:
        send_backup_email(
            recipient="backup@example.com",
            download_url="https://example.test/download",
            expires_in_days=7,
        )

    assert len(outbox) == 1
    msg = outbox[0]
    assert msg.recipients == ["backup@example.com"]
    assert msg.body is not None
    assert "https://example.test/download" in msg.body


def test_download_token_rejects_wrong_filename(backup_app):
    token = backup_routes._download_token("backup_2025.zip")

    with pytest.raises(Forbidden):
        backup_routes._validate_download_token("backup_2024.zip", token)


def test_resolve_upload_path_rejects_path_traversal(backup_app):
    with pytest.raises(ValueError):
        backup_routes._resolve_upload_path("../secret.txt")


def test_resolve_upload_path_returns_none_for_missing_file(backup_app):
    # Missing files must not raise — the backup walks thousands of
    # rows and a single missing image must not abort the whole run.
    assert backup_routes._resolve_upload_path("does/not/exist.webp") is None


def test_pg_dump_runs_non_interactively(backup_app, tmp_path):
    output_path = tmp_path / "dump.sql"

    with patch("app.routes.backup.subprocess.run") as run:
        backup_routes._run_pg_dump(output_path)

    command = run.call_args.args[0]
    assert "--format=plain" in command
    assert "--no-password" in command
    assert run.call_args.kwargs["check"] is True


def test_create_year_backup_writes_zip_and_removes_dump(backup_app, monkeypatch):
    upload_root = Path(backup_app.config["UPLOAD_FOLDER"])
    image_path = upload_root / "2025" / "2025-01-19" / "mantis.webp"
    image_path.parent.mkdir(parents=True)
    image_path.write_bytes(b"image")

    def fake_pg_dump(output_path):
        output_path.write_text("-- dump", encoding="utf-8")

    monkeypatch.setattr(
        backup_routes,
        "_image_paths_for_year",
        lambda year: [image_path],
    )
    monkeypatch.setattr(backup_routes, "_run_pg_dump", fake_pg_dump)

    backup_path = backup_routes.create_year_backup(2025)

    assert backup_path.name == "backup_2025.zip"
    with zipfile.ZipFile(backup_path) as zip_file:
        names = zip_file.namelist()
        assert "images/2025/2025-01-19/mantis.webp" in names
        assert any(
            name.startswith("dump_2025_") and name.endswith(".sql") for name in names
        )
    assert not list(Path(backup_app.config["BACKUP_DIR"]).glob("dump_2025_*.sql"))
