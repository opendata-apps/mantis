from pathlib import Path
from smtplib import SMTPException
from unittest.mock import patch


def test_backup_route_requires_post(client):
    response = client.get("/admin/backup/2025")

    assert response.status_code == 405


def test_backup_route_requires_reviewer(client):
    response = client.post("/admin/backup/2025")

    assert response.status_code == 403


def test_backup_route_creates_backup_and_sends_mail(
    app, authenticated_client, tmp_path
):
    backup_file = tmp_path / "backup_2025.zip"
    backup_file.write_bytes(b"zip")
    app.config["BACKUP_DIR"] = str(tmp_path)
    app.config["BACKUPMAIL"] = "backup@example.com"

    with (
        patch("app.routes.backup.available_backup_years", return_value=[2025]),
        patch("app.routes.backup.create_year_backup", return_value=backup_file),
        patch("app.routes.backup.send_backup_email") as send_backup_email,
    ):
        response = authenticated_client.post("/admin/backup/2025")

    assert response.status_code == 200
    assert "Backup 2025 wurde erstellt" in response.text
    assert "Backup herunterladen" in response.text
    send_backup_email.assert_called_once()
    assert send_backup_email.call_args.kwargs["recipient"] == "backup@example.com"


def test_backup_route_keeps_download_link_when_mail_fails(
    app, authenticated_client, tmp_path
):
    backup_file = tmp_path / "backup_2025.zip"
    backup_file.write_bytes(b"zip")
    app.config["BACKUP_DIR"] = str(tmp_path)
    app.config["BACKUPMAIL"] = "backup@example.com"

    with (
        patch("app.routes.backup.available_backup_years", return_value=[2025]),
        patch("app.routes.backup.create_year_backup", return_value=backup_file),
        patch(
            "app.routes.backup.send_backup_email",
            side_effect=SMTPException("smtp down"),
        ),
    ):
        response = authenticated_client.post("/admin/backup/2025")

    assert response.status_code == 200
    assert "Backup 2025 wurde erstellt" in response.text
    assert "E-Mail an backup@example.com konnte nicht gesendet werden" in response.text
    assert "Backup herunterladen" in response.text


def test_backup_download_requires_signed_token(client):
    response = client.get("/admin/backup/download/backup_2025.zip")

    assert response.status_code == 403


def test_backup_download_serves_file_with_valid_token(app, client, tmp_path):
    backup_file = Path(tmp_path) / "backup_2025.zip"
    backup_file.write_bytes(b"zip")
    app.config["BACKUP_DIR"] = str(tmp_path)

    with app.app_context():
        from app.routes.backup import _download_token

        token = _download_token(backup_file.name)

    response = client.get(f"/admin/backup/download/{backup_file.name}?token={token}")

    assert response.status_code == 200
    assert response.data == b"zip"
