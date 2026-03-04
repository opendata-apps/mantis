"""Vite integration for Flask.

Reads the Vite manifest.json and provides helper functions for templates
to include the correct hashed asset URLs with proper preload hints.

Based on Vite backend integration best practices:
https://vite.dev/guide/backend-integration
"""

import json
import os
from flask import current_app, url_for
from markupsafe import Markup


_manifest_cache = {}


def _get_manifest_path(app):
    """Get the path to the Vite manifest file."""
    return os.path.join(app.static_folder, "build", ".vite", "manifest.json")


def _load_manifest(app):
    """Load and cache the Vite manifest."""
    if app.debug:
        # Don't cache in debug mode for development
        manifest_path = _get_manifest_path(app)
        if os.path.exists(manifest_path):
            with open(manifest_path) as f:
                return json.load(f)
        return None

    # Cache in production
    if "manifest" not in _manifest_cache:
        manifest_path = _get_manifest_path(app)
        if os.path.exists(manifest_path):
            with open(manifest_path) as f:
                _manifest_cache["manifest"] = json.load(f)
        else:
            _manifest_cache["manifest"] = None

    return _manifest_cache.get("manifest")


def _collect_css_recursive(manifest, entry_key, collected=None):
    """Recursively collect all CSS files from entry and its imports."""
    if collected is None:
        collected = set()

    if entry_key not in manifest:
        return collected

    entry = manifest[entry_key]

    # Add direct CSS
    if "css" in entry:
        for css_file in entry["css"]:
            collected.add(css_file)

    # Recurse into imports
    if "imports" in entry:
        for import_key in entry["imports"]:
            _collect_css_recursive(manifest, import_key, collected)

    return collected


def _collect_imports_recursive(manifest, entry_key, collected=None):
    """Recursively collect all imported JS chunks for modulepreload."""
    if collected is None:
        collected = set()

    if entry_key not in manifest:
        return collected

    entry = manifest[entry_key]

    # Add imports (not the entry itself)
    if "imports" in entry:
        for import_key in entry["imports"]:
            if import_key in manifest:
                collected.add(manifest[import_key]["file"])
                _collect_imports_recursive(manifest, import_key, collected)

    return collected


def vite_asset(entry: str) -> str:
    """Get the URL for a Vite asset.

    Args:
        entry: Entry point name relative to app/static/
               e.g., 'js/vendor.js', 'css/theme.css'

    Returns:
        URL string with hashed filename in production,
        or original path in development
    """
    manifest = _load_manifest(current_app)

    if manifest and entry in manifest:
        hashed_file = manifest[entry]["file"]
        return url_for("static", filename=f"build/{hashed_file}")

    # Fallback: return unbundled path
    return url_for("static", filename=entry)


def vite_css(entry: str) -> list:
    """Get all CSS URLs associated with a JS entry point (including imports).

    Args:
        entry: JS entry point (e.g., 'js/report-form.js')

    Returns:
        List of CSS URLs (includes CSS from imported chunks)
    """
    manifest = _load_manifest(current_app)

    if not manifest or entry not in manifest:
        return []

    # Collect CSS from entry and all its imports recursively
    css_files = _collect_css_recursive(manifest, entry)

    return [
        url_for("static", filename=f"build/{css_file}")
        for css_file in sorted(css_files)  # Sort for consistent ordering
    ]


def vite_preload(entry: str) -> Markup:
    """Generate modulepreload link tags for a JS entry's imports.

    This improves load performance by preloading imported chunks
    before the browser discovers them during JS execution.

    Args:
        entry: JS entry point (e.g., 'js/map.js')

    Returns:
        Markup containing <link rel="modulepreload"> tags
    """
    manifest = _load_manifest(current_app)

    if not manifest or entry not in manifest:
        return Markup("")

    # Collect all imported chunks
    import_files = _collect_imports_recursive(manifest, entry)

    if not import_files:
        return Markup("")

    links = []
    for file in sorted(import_files):
        url = url_for("static", filename=f"build/{file}")
        links.append(f'<link rel="modulepreload" href="{url}">')

    return Markup("\n".join(links))


def vite_font_preloads(*patterns: str) -> Markup:
    """Generate <link rel="preload"> tags for font files matching patterns.

    Searches the Vite manifest for font entries whose keys contain any of
    the given substrings and returns preload tags for them.

    Args:
        *patterns: Substrings to match against manifest keys,
                   e.g. 'inter-latin-wght-normal', 'inter-latin-wght-italic'

    Returns:
        Markup containing <link rel="preload" as="font"> tags
    """
    manifest = _load_manifest(current_app)
    if not manifest:
        return Markup("")

    links = []
    for key, entry in manifest.items():
        if key.endswith(".woff2") and any(p in key for p in patterns):
            font_url = url_for("static", filename=f"build/{entry['file']}")
            links.append(
                f'<link rel="preload" as="font" type="font/woff2"'
                f' crossorigin href="{font_url}">'
            )
    return Markup("\n".join(sorted(links)))


def vite_tags(entry: str) -> Markup:
    """Generate all required tags for a JS entry point.

    Includes:
    - CSS link tags (from entry and imports)
    - Modulepreload hints for imported chunks
    - Script tag for the entry

    Args:
        entry: JS entry point (e.g., 'js/map.js')

    Returns:
        Markup containing all necessary HTML tags
    """
    manifest = _load_manifest(current_app)

    if not manifest or entry not in manifest:
        # Fallback for development
        return Markup(
            f'<script type="module" src="{url_for("static", filename=entry)}"></script>'
        )

    tags = []

    # CSS tags
    for css_url in vite_css(entry):
        tags.append(f'<link rel="stylesheet" href="{css_url}">')

    # Modulepreload hints
    preload = vite_preload(entry)
    if preload:
        tags.append(str(preload))

    # Main script tag (type="module" for ES module support)
    script_url = vite_asset(entry)
    tags.append(f'<script type="module" src="{script_url}"></script>')

    return Markup("\n".join(tags))


def init_app(app):
    """Initialize Vite helpers for Flask app."""

    @app.context_processor
    def vite_context():
        return {
            "vite_asset": vite_asset,
            "vite_css": vite_css,
            "vite_preload": vite_preload,
            "vite_font_preloads": vite_font_preloads,
            "vite_tags": vite_tags,
        }
