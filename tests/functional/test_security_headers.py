"""Security header invariants.

The response must carry a Content-Security-Policy that does NOT permit
`unsafe-eval`. htmx's eval-based attribute features (`hx-on::*`,
`hx-vals "js:"`, `hx-headers "js:"`, trigger filters) are gated off via
`allowEval: false` in layout.html's htmx-config meta tag; if anyone
re-introduces them, this test plus the template scan below catches it.
"""

from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "app" / "templates"


def test_csp_header_present_and_omits_unsafe_eval(client):
    resp = client.get("/")
    csp = resp.headers.get("Content-Security-Policy", "")

    assert csp, "Content-Security-Policy header must be set"
    assert "'unsafe-eval'" not in csp, (
        "CSP must not allow 'unsafe-eval' — htmx eval features are disabled "
        "via the htmx-config meta tag in layout.html."
    )
    assert "default-src 'self'" in csp
    assert "object-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "worker-src 'self' blob:" in csp


def test_csp_script_src_blocks_inline_scripts(client):
    """Behaviour lives in the Vite modules, so the browser may refuse every
    inline <script> and on*= handler — the main defence against injected markup."""
    csp = client.get("/").headers["Content-Security-Policy"]
    script_src = next(d for d in csp.split("; ") if d.startswith("script-src "))

    assert "'unsafe-inline'" not in script_src


def test_x_xss_protection_is_explicitly_disabled(client):
    """Absent is not the same as "0" — a legacy browser then uses its default.

    OWASP Secure Headers asks for the explicit "0".
    """
    resp = client.get("/")
    assert resp.headers.get("X-XSS-Protection") == "0"


def test_responses_prevent_referrer_disclosure(client):
    for path in ("/melden", "/missing/private-bearer"):
        response = client.get(path)
        assert response.headers.get("Referrer-Policy") == "strict-origin"


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
