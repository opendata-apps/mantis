"""Security header invariants.

These tests pin down two CSP-relevant guarantees:

1. The response carries a Content-Security-Policy that does NOT permit
   `unsafe-eval`. htmx's eval-based attribute features
   (`hx-on::*`, `hx-vals "js:"`, `hx-headers "js:"`, trigger filters)
   are gated off via `htmx.config.allowEval = false`; if anyone
   re-introduces them, this test plus the template scan below catches it.

2. The deprecated `X-XSS-Protection` header is explicitly disabled
   (OWASP recommendation — the legacy filter can introduce XSS itself).
"""

from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "app" / "templates"


def test_csp_header_present_and_omits_unsafe_eval(client):
    resp = client.get("/")
    csp = resp.headers.get("Content-Security-Policy", "")

    assert csp, "Content-Security-Policy header must be set"
    assert "'unsafe-eval'" not in csp, (
        "CSP must not allow 'unsafe-eval' — htmx eval features are disabled "
        "via htmx.config.allowEval = false in every JS entrypoint."
    )
    assert "default-src 'self'" in csp
    assert "object-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "worker-src 'self' blob:" in csp


def test_x_xss_protection_is_disabled(client):
    resp = client.get("/")
    assert resp.headers.get("X-XSS-Protection") == "0", (
        "X-XSS-Protection is deprecated and can introduce XSS bugs; "
        "set to '0' per OWASP Secure Headers."
    )


def test_no_template_uses_eval_based_htmx_attributes():
    """Static guard: regress if a template re-introduces htmx eval features."""
    forbidden_substrings = (
        "hx-on::",  # inline JS expression on htmx events
        "hx-vals='js:",  # JS-evaluated values
        'hx-vals="js:',
        "hx-headers='js:",  # JS-evaluated headers
        'hx-headers="js:',
    )

    offenders: list[tuple[Path, str]] = []
    for path in TEMPLATES_DIR.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        for needle in forbidden_substrings:
            if needle in text:
                offenders.append((path.relative_to(TEMPLATES_DIR), needle))

    assert not offenders, (
        "Templates must not use htmx eval-based features "
        "(would require 'unsafe-eval' in CSP):\n  "
        + "\n  ".join(f"{p}: {n}" for p, n in offenders)
    )
