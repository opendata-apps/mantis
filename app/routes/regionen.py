from pathlib import Path

import yaml
from flask import Blueprint, abort, render_template

regionen = Blueprint("regionen", __name__)

CONTENT_DIR = Path(__file__).parent.parent / "content" / "regionen"


def _load_region(slug: str) -> dict | None:
    """Region content from its YAML file, or None if there is none."""
    try:
        with open(CONTENT_DIR / f"{slug}.yaml", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return None


@regionen.route("/gottesanbeterin-in-<slug>/")
def region_page(slug: str):
    """Render a regional landing page."""
    region = _load_region(slug)
    if region is None:
        abort(404)

    parent = _load_region(region["parent"]) if region.get("parent") else None
    siblings = [_load_region(s) for s in region.get("siblings", [])]
    children = [_load_region(c) for c in region.get("children", [])]

    return render_template(
        "region.html",
        region=region,
        parent=parent,
        siblings=[s for s in siblings if s],
        children=[c for c in children if c],
    )
