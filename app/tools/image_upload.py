"""What counts as an uploadable photo — the one place that decides.

Everything below is derived from ``IMAGE_TYPES``. Templates reach it through
the ``upload_config`` Jinja global, the browser through the JSON block the
photo macro renders.
"""

from typing import Any

# Extension → MIME type, in the order the formats should be listed to a
# reporter. jpeg shares a MIME with jpg, so it adds an accepted extension
# without adding a format.
IMAGE_TYPES: dict[str, str] = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "heic": "image/heic",
    "heif": "image/heif",
}

# The photo alone. Config's MAX_CONTENT_LENGTH is deliberately larger: it has
# to fit the rest of the form fields alongside the file.
MAX_UPLOAD_BYTES = 12 * 1024 * 1024


def pillow_formats() -> list[str]:
    """Pillow format names for ``Image.open(formats=...)``.

    Without the list Pillow sniffs any format it knows (TIFF, PSD, JPEG 2000,
    …) whatever the filename says. Read from Pillow's registry, so HEIF only
    appears once pillow-heif has registered; the app factory asserts it did.
    """
    from PIL import Image

    Image.init()
    mimes = set(IMAGE_TYPES.values())
    return [fmt for fmt, mime in Image.MIME.items() if mime in mimes]


def allowed_extensions() -> list[str]:
    """Extensions for FileAllowed, without the leading dot."""
    return list(IMAGE_TYPES)


def display_formats() -> list[str]:
    """One label per distinct format: JPG, PNG, WEBP, HEIC, HEIF."""
    first_extension: dict[str, str] = {}
    for extension, mime in IMAGE_TYPES.items():
        first_extension.setdefault(mime, extension.upper())
    return list(first_extension.values())


def accept_attribute() -> str:
    """Value for the file input's ``accept``.

    MIME types lead: Android pickers ignore extension-only accept lists and can
    end up greying out every file in the gallery.
    """
    mimes = dict.fromkeys(IMAGE_TYPES.values())
    return ",".join([*mimes, *(f".{ext}" for ext in IMAGE_TYPES)])


def extension_by_mime() -> dict[str, str]:
    """MIME → the extension to save it under, e.g. image/jpeg → jpg.

    Derived here rather than in the browser: serialising IMAGE_TYPES sorts its
    keys, which would make "jpeg" beat "jpg" for the shared MIME type.
    """
    reversed_map: dict[str, str] = {}
    for extension, mime in IMAGE_TYPES.items():
        reversed_map.setdefault(mime, extension)
    return reversed_map


def max_upload_mb() -> int:
    return MAX_UPLOAD_BYTES // (1024 * 1024)


def upload_config() -> dict[str, Any]:
    """The photo rules as the template and the browser consume them."""
    return {
        "types": IMAGE_TYPES,
        "extensionByMime": extension_by_mime(),
        "maxBytes": MAX_UPLOAD_BYTES,
        "maxMb": max_upload_mb(),
        "accept": accept_attribute(),
        "formats": display_formats(),
    }
