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


def _warn_missing_entry(entry: str) -> None:
    """Report a manifest miss instead of emitting an unusable asset URL.

    Dev runs `vite build --watch`, which writes the same manifest as a
    production build, so there is no mode where the raw source path works —
    it would serve an ES module with unresolvable bare imports and render a
    silently broken page.
    """
    current_app.logger.error(
        f"Vite manifest has no entry for {entry!r} — run `bun run build`."
    )


def vite_asset(entry: str) -> str:
    """Get the URL for a Vite asset.

    Args:
        entry: Entry point name relative to app/static/
               e.g., 'js/vendor.js', 'css/theme.css'

    Returns:
        URL string with the hashed filename from the manifest.
    """
    manifest = _load_manifest(current_app)

    if manifest and entry in manifest:
        hashed_file = manifest[entry]["file"]
        return url_for("static", filename=f"build/{hashed_file}")

    _warn_missing_entry(entry)
    return ""


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

    Emits stylesheets, the entry script, then modulepreload hints for the
    imported chunks — the order Vite's backend integration guide recommends
    for optimal performance.
    https://vite.dev/guide/backend-integration

    Args:
        entry: JS entry point (e.g., 'js/map.js')

    Returns:
        Markup containing all necessary HTML tags
    """
    manifest = _load_manifest(current_app)

    if not manifest or entry not in manifest:
        _warn_missing_entry(entry)
        return Markup("")

    tags = []

    css_files = _collect_css_recursive(manifest, entry)
    for css_file in sorted(css_files):
        css_url = url_for("static", filename=f"build/{css_file}")
        tags.append(f'<link rel="stylesheet" href="{css_url}">')

    hashed_file = manifest[entry]["file"]
    script_url = url_for("static", filename=f"build/{hashed_file}")
    tags.append(f'<script type="module" src="{script_url}"></script>')

    for file in sorted(_collect_imports_recursive(manifest, entry)):
        preload_url = url_for("static", filename=f"build/{file}")
        tags.append(f'<link rel="modulepreload" href="{preload_url}">')

    return Markup("\n".join(tags))


def init_app(app):
    """Initialize Vite helpers for Flask app."""

    @app.context_processor
    def vite_context():
        return {
            "vite_asset": vite_asset,
            "vite_font_preloads": vite_font_preloads,
            "vite_tags": vite_tags,
        }
