import os
from smtplib import SMTPException
import subprocess
import tempfile
import zipfile
from datetime import date
from pathlib import Path

from flask import (
    Blueprint,
    abort,
    current_app,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import func, select

from app import db
from app.auth import reviewer_required
from app.database.models import TblFundorte, TblMeldungen
from app.tools.send_backup_email import send_backup_email


backup = Blueprint("backup", __name__, url_prefix="/admin/backup")


def available_backup_years() -> list[int]:
    min_map_date = date(current_app.config["MIN_MAP_YEAR"], 1, 1)
    years_stmt = (
        select(func.extract("year", TblMeldungen.dat_fund_von).label("year"))
        .where(TblMeldungen.dat_fund_von >= min_map_date)
        .distinct()
        .order_by("year")
    )
    return [int(row[0]) for row in db.session.execute(years_stmt).all()]


def _backup_dir() -> Path:
    backup_dir = Path(current_app.config["BACKUP_DIR"])
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"],
        salt="backup-download",
    )


def _download_token(filename: str) -> str:
    return _serializer().dumps({"filename": filename})


def _validate_download_token(filename: str, token: str | None) -> None:
    if not token:
        abort(403)
    try:
        data = _serializer().loads(
            token,
            max_age=current_app.config["BACKUP_DOWNLOAD_MAX_AGE_SECONDS"],
        )
    except (BadSignature, SignatureExpired):
        abort(403)
    if data.get("filename") != filename:
        abort(403)


def _resolve_upload_path(relative_path: str) -> Path:
    upload_root = Path(current_app.config["UPLOAD_FOLDER"]).resolve()
    image_path = (upload_root / relative_path).resolve()
    if not image_path.is_relative_to(upload_root):
        raise ValueError(f"Unsafe upload path in database: {relative_path!r}")
    if not image_path.is_file():
        raise FileNotFoundError(f"Upload file missing: {relative_path}")
    return image_path


def _image_paths_for_year(year: int) -> list[Path]:
    start = date(year, 1, 1)
    end = date(year + 1, 1, 1)
    stmt = (
        select(TblFundorte.ablage)
        .join(TblMeldungen, TblMeldungen.fo_zuordnung == TblFundorte.id)
        .where(TblMeldungen.dat_fund_von >= start, TblMeldungen.dat_fund_von < end)
        .order_by(TblMeldungen.id)
    )
    return [_resolve_upload_path(path) for path in db.session.scalars(stmt)]


def _run_pg_dump(output_path: Path) -> None:
    command = [
        "pg_dump",
        "-h",
        current_app.config["DATABASE_HOST"],
        "-p",
        current_app.config["DATABASE_PORT"],
        "-U",
        current_app.config["DATABASE_USER"],
        "-d",
        current_app.config["DATABASE_DB"],
        "--format=plain",
        "--no-password",
    ]
    env = {**os.environ, "PGPASSWORD": current_app.config["DATABASE_PASSWORD"]}
    with output_path.open("w") as dump_file:
        subprocess.run(command, env=env, stdout=dump_file, check=True)


def create_year_backup(year: int) -> Path:
    backup_dir = _backup_dir()
    filename = f"backup_{year}.zip"
    final_path = backup_dir / filename
    image_paths = _image_paths_for_year(year)

    dump_path: Path | None = None
    temp_zip_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f"dump_{year}_",
            suffix=".sql",
            dir=backup_dir,
            delete=False,
        ) as dump_file:
            dump_path = Path(dump_file.name)

        _run_pg_dump(dump_path)

        with tempfile.NamedTemporaryFile(
            prefix=f".backup_{year}_",
            suffix=".zip",
            dir=backup_dir,
            delete=False,
        ) as temp_zip_file:
            temp_zip_path = Path(temp_zip_file.name)

        with zipfile.ZipFile(temp_zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for image_path in image_paths:
                zip_file.write(
                    image_path,
                    Path("images")
                    / image_path.relative_to(
                        Path(current_app.config["UPLOAD_FOLDER"]).resolve()
                    ),
                )
            zip_file.write(dump_path, dump_path.name)

        os.replace(temp_zip_path, final_path)
        temp_zip_path = None
        return final_path
    finally:
        if dump_path:
            dump_path.unlink(missing_ok=True)
        if temp_zip_path:
            temp_zip_path.unlink(missing_ok=True)


@backup.post("/<int:year>")
@reviewer_required
def trigger_year_backup(year: int):
    if year not in available_backup_years():
        abort(404)

    recipient = current_app.config["BACKUPMAIL"]
    if not recipient:
        current_app.logger.error("BACKUPMAIL is not configured.")
        return render_template("admin/partials/_backup_status.html", error=True), 500

    try:
        backup_path = create_year_backup(year)
    except (
        FileNotFoundError,
        OSError,
        subprocess.CalledProcessError,
        ValueError,
    ):
        current_app.logger.exception("Backup for year %s failed.", year)
        return render_template("admin/partials/_backup_status.html", error=True), 500

    token = _download_token(backup_path.name)
    download_url = url_for(
        "backup.download_backup",
        filename=backup_path.name,
        token=token,
        _external=True,
    )
    expires_in_days = current_app.config["BACKUP_DOWNLOAD_MAX_AGE_SECONDS"] // 86400

    try:
        send_backup_email(
            recipient=recipient,
            download_url=download_url,
            expires_in_days=expires_in_days,
        )
    except (OSError, SMTPException):
        current_app.logger.exception("Backup mail for year %s failed.", year)
        return render_template(
            "admin/partials/_backup_status.html",
            error=False,
            mail_error=True,
            year=year,
            recipient=recipient,
            download_url=download_url,
        )

    return render_template(
        "admin/partials/_backup_status.html",
        error=False,
        mail_error=False,
        year=year,
        recipient=recipient,
        download_url=download_url,
    )


@backup.get("/download/<path:filename>")
def download_backup(filename: str):
    _validate_download_token(filename, request.args.get("token"))
    return send_from_directory(
        _backup_dir(),
        filename,
        as_attachment=True,
        download_name=Path(filename).name,
    )
