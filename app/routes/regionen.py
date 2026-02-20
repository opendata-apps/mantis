import os

import yaml
from flask import Blueprint, abort, render_template, url_for

regionen = Blueprint("regionen", __name__)

CONTENT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "content", "regionen"
)


def _load_region(slug: str) -> dict:
    """Load region content from YAML file. Returns dict or raises FileNotFoundError."""
    filepath = os.path.join(CONTENT_DIR, f"{slug}.yaml")
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"No content file for region: {slug}")
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_region_safe(slug: str) -> dict | None:
    """Load region content, returning None if not found."""
    try:
        return _load_region(slug)
    except FileNotFoundError:
        return None


@regionen.route("/gottesanbeterin-in-<slug>/")
def region_page(slug: str):
    """Render a regional landing page."""
    try:
        region = _load_region(slug)
    except FileNotFoundError:
        abort(404)

    # Load parent for breadcrumb
    parent = None
    if region.get("parent"):
        parent = _load_region_safe(region["parent"])

    # Load sibling regions for cross-linking
    siblings = []
    for sib_slug in region.get("siblings", []):
        sib = _load_region_safe(sib_slug)
        if sib:
            siblings.append(sib)

    # Load children for sub-region linking
    children = []
    for child_slug in region.get("children", []):
        child = _load_region_safe(child_slug)
        if child:
            children.append(child)

    return render_template(
        "region.html",
        region=region,
        parent=parent,
        siblings=siblings,
        children=children,
    )
