import fcntl
import io
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

from flask import current_app
from PIL import Image, ImageFile, ImageOps
from werkzeug.utils import secure_filename

from app.tools.image_upload import PILLOW_FORMATS

# Long side of a stored photo; a larger upload is downscaled to it.
MAX_STORED_DIMENSION = 2048
# Covers 48/50 MP phone originals. HEIC has no reduced decode and costs about
# 12 bytes per pixel, so this cap is what bounds a worker's memory.
MAX_UPLOAD_PIXELS = 50_000_000
TOO_LARGE_MESSAGE = (
    "Das Foto darf höchstens 50 Megapixel haben. "
    "Bitte verkleinern Sie es und wählen Sie es erneut aus."
)

# A mobile upload that loses its last bytes still carries the whole animal, so
# decode what arrived; a frame damaged beyond use still fails the blank-pixel
# check below. ty infers the flag as Literal[False] though it exists to be set.
ImageFile.LOAD_TRUNCATED_IMAGES = True  # ty: ignore[invalid-assignment]


class InvalidImageError(ValueError):
    """The upload cannot be processed as a report photo."""


class BlankImageError(InvalidImageError):
    """The uploaded frame has no visible pixels."""


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


def _has_no_visible_pixels(img):
    """True when every pixel is fully transparent.

    An Android WebView can drop ``drawImage`` without raising, and the canvas is
    then encoded at full size still holding its initial value — transparent
    black. Such a frame is worthless to a reviewer but looks like a valid image
    file, so it has to be caught by content rather than by byte size (report
    21953 was 22KB, twice the client-side size threshold).
    """
    if not img.has_transparency_data:
        return False
    # RGBA/LA already carry alpha as a band; only palette transparency needs a
    # convert to read it.
    alpha = (
        img.getchannel("A")
        if img.mode in ("RGBA", "LA")
        else img.convert("RGBA").getchannel("A")
    )
    return alpha.getextrema() == (0, 0)


@contextmanager
def _image_decode_slot(upload_root: Path):
    """One decoder across all workers sharing this upload directory."""
    with (upload_root / ".image-decode.lock").open("a") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        yield


def process_uploaded_image(photo_file, sighting_date, city_name, user_id):
    """Process uploaded image - trust client-optimized WebP files to avoid double compression."""
    upload_root = Path(current_app.config["UPLOAD_FOLDER"])
    upload_dir = ensure_upload_dir(upload_root, sighting_date)
    filename = build_upload_filename(city_name, user_id, datetime.now())
    full_path = upload_dir / filename

    image_bytes = photo_file.read()

    try:
        with (
            _image_decode_slot(upload_root),
            Image.open(io.BytesIO(image_bytes), formats=PILLOW_FORMATS) as img,
        ):
            if img.width * img.height > MAX_UPLOAD_PIXELS:
                raise InvalidImageError(TOO_LARGE_MESSAGE)
            # JPEG only, a no-op otherwise: libjpeg decodes at 1/2–1/8 scale, so
            # a 48 MP original costs ~90 MiB instead of ~260. Must precede load().
            img.draft("RGB", (MAX_STORED_DIMENSION, MAX_STORED_DIMENSION))
            img.load()
            if _has_no_visible_pixels(img):
                raise BlankImageError("uploaded frame has no visible pixels")

            if img.format == "WEBP" and max(img.size) <= MAX_STORED_DIMENSION:
                # Preserve client-optimized WebP without recompressing it.
                image_bytes_to_save = image_bytes
            else:
                # A browser bakes EXIF orientation into the canvas, but an original
                # uploaded by the conversion fallback arrives untouched and the WebP
                # re-encode drops the tag — so rotate here or a portrait photo is
                # archived sideways with nothing left to fix it.
                output_buffer = io.BytesIO()
                ImageOps.exif_transpose(img, in_place=True)
                # An original forwarded by the conversion fallback has had no
                # client-side downscale; a 12MP frame would re-encode to ~0.9MB.
                img.thumbnail((MAX_STORED_DIMENSION, MAX_STORED_DIMENSION))
                img.save(output_buffer, format="WEBP", quality=60)
                image_bytes_to_save = output_buffer.getvalue()
    except InvalidImageError:
        raise
    except Image.DecompressionBombError as error:
        # Pillow refuses above ~179 MP before our own cap is reached.
        raise InvalidImageError(TOO_LARGE_MESSAGE) from error
    except (OSError, ValueError) as error:
        raise InvalidImageError(
            "Das Foto konnte nicht gelesen werden. Bitte wählen Sie ein anderes Foto."
        ) from error

    tmp_path = full_path.with_name(full_path.name + ".part")
    try:
        tmp_path.write_bytes(image_bytes_to_save)
        tmp_path.replace(full_path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise

    return str(full_path.relative_to(upload_root))
