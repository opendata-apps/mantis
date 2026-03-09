from datetime import date, datetime
from pathlib import Path

from werkzeug.utils import secure_filename


def build_upload_subdir(sighting_date: date | datetime) -> Path:
    """Return the year/date upload subdirectory for a sighting."""
    return Path(sighting_date.strftime("%Y")) / sighting_date.strftime("%Y-%m-%d")


def ensure_upload_dir(upload_root: Path, sighting_date: date | datetime) -> Path:
    """Create and return the upload directory for a sighting date."""
    upload_dir = upload_root / build_upload_subdir(sighting_date)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def build_upload_filename(
    location: str | None,
    user_id: str,
    timestamp: date | datetime,
) -> str:
    """Build the canonical report image filename."""
    location_part = secure_filename(location or "unknown_city")
    user_part = secure_filename(user_id)
    timestamp_part = timestamp.strftime("%Y%m%d%H%M%S")
    return f"{location_part}-{timestamp_part}-{user_part}.webp"
