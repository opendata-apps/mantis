# Regional Landing Pages Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build 3 SEO-optimized regional landing pages (Deutschland, Brandenburg, Berlin) using YAML content files and a single shared Jinja2 template.

**Architecture:** New Flask Blueprint `regionen` with a single dynamic route `/gottesanbeterin-in-<slug>/`. Content stored in YAML files under `app/content/regionen/`. One shared template `region.html` renders all pages with full SEO blocks (OG, Twitter, JSON-LD schema, breadcrumbs).

**Tech Stack:** Flask Blueprint, PyYAML, Jinja2, Tailwind CSS (existing classes), pytest

**Design Doc:** `docs/plans/2026-02-20-regional-pages-design.md`

---

### Task 1: Add PyYAML dependency

**Files:**
- Modify: `pyproject.toml:7-36` (dependencies list)

**Step 1: Add pyyaml to dependencies**

In `pyproject.toml`, add `"pyyaml>=6.0"` to the `dependencies` list (after `psycopg`):

```toml
    "psycopg[binary]>=3.2",
    "pyyaml>=6.0",
    "python-dateutil>=2.9.0.post0",
```

**Step 2: Install**

Run: `cd /Users/leon/Documents/projects/mantis/mantis && uv sync`
Expected: Resolves and installs pyyaml

**Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add pyyaml dependency for regional content files"
```

---

### Task 2: Create the Flask Blueprint route handler

**Files:**
- Create: `app/routes/regionen.py`
- Modify: `app/__init__.py:262-275` (blueprint registration)

**Step 1: Write the failing test**

Create `tests/functional/test_regionen.py`:

```python
import pytest


def test_region_page_returns_200_for_valid_slug(client):
    """Regional page for a known slug returns 200."""
    response = client.get("/gottesanbeterin-in-deutschland/")
    assert response.status_code == 200


def test_region_page_returns_404_for_unknown_slug(client):
    """Regional page for unknown slug returns 404."""
    response = client.get("/gottesanbeterin-in-atlantis/")
    assert response.status_code == 404


def test_region_page_contains_title(client):
    """Regional page contains the page title from YAML."""
    response = client.get("/gottesanbeterin-in-deutschland/")
    assert b"Gottesanbeterin in Deutschland" in response.data


def test_region_page_contains_meta_description(client):
    """Regional page has a meta description."""
    response = client.get("/gottesanbeterin-in-brandenburg/")
    assert b'<meta name="description"' in response.data
    assert b"Brandenburg" in response.data


def test_region_page_contains_breadcrumbs(client):
    """Regional page contains breadcrumb navigation."""
    response = client.get("/gottesanbeterin-in-brandenburg/")
    assert b"BreadcrumbList" in response.data


def test_region_page_contains_cta(client):
    """Regional page contains call-to-action to report form."""
    response = client.get("/gottesanbeterin-in-berlin/")
    assert b"/melden" in response.data


def test_region_page_contains_canonical(client):
    """Regional page has a canonical URL."""
    response = client.get("/gottesanbeterin-in-deutschland/")
    assert b"canonical" in response.data
    assert b"gottesanbeterin-in-deutschland" in response.data


def test_region_page_contains_sections(client):
    """Regional page renders content sections."""
    response = client.get("/gottesanbeterin-in-deutschland/")
    assert b"Verbreitung" in response.data


def test_region_page_contains_sibling_links(client):
    """Brandenburg page links to Berlin (sibling)."""
    response = client.get("/gottesanbeterin-in-brandenburg/")
    assert b"gottesanbeterin-in-berlin" in response.data


def test_region_page_trailing_slash_redirect(client):
    """URL without trailing slash redirects to URL with slash."""
    response = client.get("/gottesanbeterin-in-deutschland")
    assert response.status_code in (301, 308)
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/leon/Documents/projects/mantis/mantis && uv run pytest tests/functional/test_regionen.py -v`
Expected: FAIL — routes don't exist yet

**Step 3: Create the route handler**

Create `app/routes/regionen.py`:

```python
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
```

**Step 4: Register the blueprint**

In `app/__init__.py`, add after the existing blueprint imports (around line 267):

```python
from app.routes.regionen import regionen
```

And add after the existing `register_blueprint` calls (around line 275):

```python
app.register_blueprint(regionen)
```

**Step 5: Create empty content directory**

Run: `mkdir -p /Users/leon/Documents/projects/mantis/mantis/app/content/regionen`

**Step 6: Commit route handler**

```bash
git add app/routes/regionen.py app/__init__.py tests/functional/test_regionen.py
git commit -m "feat(regionen): add Flask blueprint for regional landing pages"
```

---

### Task 3: Create the region.html template

**Files:**
- Create: `app/templates/region.html`

**Reference:** Use the same CSS classes as existing content pages (impressum.html, datenschutz.html, mantis_religiosa.html):
- Container: `container max-w-5xl px-4 py-16 mx-auto`
- Headings: `section-heading` (H2)
- Body text: `prose-content-spaced`
- Buttons: `btn-primary group relative overflow-hidden rounded-md`
- Cards: `p-8 rounded-lg shadow-xl bg-green-50`

**Step 1: Create the template**

Create `app/templates/region.html`:

```html
{% extends "layout.html" %}

{% block page_title %}{{ region.title }} | Gottesanbeterin Gesucht{% endblock %}

{% block meta_description %}{{ region.meta_description }}{% endblock %}

{% block canonical %}{{ url_for('regionen.region_page', slug=region.slug, _external=True) }}{% endblock %}

{% block og_meta %}
<meta property="og:title" content="{{ region.og_title }}" />
<meta property="og:type" content="article" />
<meta property="og:url" content="{{ url_for('regionen.region_page', slug=region.slug, _external=True) }}" />
<meta property="og:image" content="{{ url_for('static', filename='images/berger03.webp', _external=True) }}" />
<meta property="og:description" content="{{ region.meta_description }}" />
<meta property="og:site_name" content="Gottesanbeterin Gesucht" />
<meta property="og:locale" content="de_DE" />
{% endblock %}

{% block twitter_meta %}
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{{ region.og_title }}" />
<meta name="twitter:description" content="{{ region.meta_description }}" />
<meta name="twitter:image" content="{{ url_for('static', filename='images/berger03.webp', _external=True) }}" />
{% endblock %}

{% block head %}
{{ super() }}
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "{{ url_for('regionen.region_page', slug=region.slug, _external=True) }}"
  },
  "headline": "{{ region.title }}",
  "description": "{{ region.meta_description }}",
  "image": "{{ url_for('static', filename='images/berger03.webp', _external=True) }}",
  "author": {
    "@type": "Organization",
    "name": "Gottesanbeterin Gesucht"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Gottesanbeterin Gesucht",
    "logo": {
      "@type": "ImageObject",
      "url": "{{ url_for('static', filename='images/favicon/apple-touch-icon.png', _external=True) }}"
    }
  },
  "datePublished": "2026-02-20",
  "dateModified": "2026-02-20"
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Startseite",
      "item": "{{ url_for('main.index', _external=True) }}"
    }{% if parent %},
    {
      "@type": "ListItem",
      "position": 2,
      "name": "{{ parent.title }}",
      "item": "{{ url_for('regionen.region_page', slug=parent.slug, _external=True) }}"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "{{ region.title }}"
    }{% else %},
    {
      "@type": "ListItem",
      "position": 2,
      "name": "{{ region.title }}"
    }{% endif %}
  ]
}
</script>
{% endblock %}

{% block title %}{{ region.title }}{% endblock %}

{% block content %}
<div class="container max-w-5xl px-4 py-16 mx-auto">

    {# Breadcrumb navigation #}
    <nav aria-label="Breadcrumb" class="mb-8">
        <ol class="flex items-center space-x-2 text-sm text-gray-500">
            <li><a href="{{ url_for('main.index') }}" class="text-green-700 hover:underline">Startseite</a></li>
            {% if parent %}
            <li><span class="mx-1">/</span></li>
            <li><a href="{{ url_for('regionen.region_page', slug=parent.slug) }}" class="text-green-700 hover:underline">{{ parent.name }}</a></li>
            {% endif %}
            <li><span class="mx-1">/</span></li>
            <li class="text-gray-700 font-medium" aria-current="page">{{ region.name }}</li>
        </ol>
    </nav>

    {# Intro paragraph #}
    <div class="mb-12">
        <p class="prose-content-spaced text-lg leading-relaxed">{{ region.intro }}</p>
    </div>

    {# Content sections #}
    {% for section in region.sections %}
    <div class="mb-12">
        <h2 class="section-heading">{{ section.heading }}</h2>
        <div class="prose-content-spaced">{{ section.content | safe }}</div>
    </div>
    {% endfor %}

    {# Call to action #}
    <div class="p-8 mb-12 text-center rounded-lg shadow-xl bg-green-50">
        <h2 class="mb-4 text-2xl font-bold text-green-800">{{ region.cta_text }}</h2>
        <p class="mb-6 text-lg text-gray-700">Haben Sie eine Gottesanbeterin in {{ region.name }} entdeckt? Helfen Sie der Forschung und melden Sie Ihre Beobachtung!</p>
        <a href="{{ region.cta_url }}" class="btn-primary group relative overflow-hidden rounded-md">
            <span class="relative z-10">Jetzt melden</span>
            <svg class="w-5 h-5 ml-2 -mr-1 transition-transform duration-300 group-hover:translate-x-1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
            <div class="absolute inset-0 w-full h-full transition-all duration-300 scale-0 rounded-md group-hover:scale-100 group-hover:bg-white/10"></div>
        </a>
    </div>

    {# Related regions #}
    {% if siblings or children %}
    <div class="mb-12">
        <h2 class="section-heading">Weitere Regionen</h2>
        <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {% for sib in siblings %}
            <a href="{{ url_for('regionen.region_page', slug=sib.slug) }}" class="block p-6 transition-shadow bg-white rounded-lg shadow-md hover:shadow-lg">
                <h3 class="text-lg font-semibold text-green-700">{{ sib.title }}</h3>
                <p class="mt-2 text-sm text-gray-600">{{ sib.meta_description[:100] }}...</p>
            </a>
            {% endfor %}
            {% for child in children %}
            <a href="{{ url_for('regionen.region_page', slug=child.slug) }}" class="block p-6 transition-shadow bg-white rounded-lg shadow-md hover:shadow-lg">
                <h3 class="text-lg font-semibold text-green-700">{{ child.title }}</h3>
                <p class="mt-2 text-sm text-gray-600">{{ child.meta_description[:100] }}...</p>
            </a>
            {% endfor %}
        </div>
    </div>
    {% endif %}

    {# Cross-links to other site sections #}
    <div class="pt-8 mt-8 border-t border-gray-200">
        <p class="text-sm text-gray-500">
            Mehr erfahren:
            <a href="/mantis-religiosa" class="text-green-700 hover:underline">Über die Gottesanbeterin</a> ·
            <a href="/bestimmung" class="text-green-700 hover:underline">Bestimmungsschlüssel</a> ·
            <a href="/faq" class="text-green-700 hover:underline">Häufige Fragen</a>
        </p>
    </div>
</div>
{% endblock content %}
```

**Step 2: Run tests to verify they pass**

Run: `cd /Users/leon/Documents/projects/mantis/mantis && uv run pytest tests/functional/test_regionen.py -v`
Expected: Tests still fail because YAML content files don't exist yet.
(That's expected — Task 4 creates the content files.)

**Step 3: Commit template**

```bash
git add app/templates/region.html
git commit -m "feat(regionen): add shared region template with SEO blocks and breadcrumbs"
```

---

### Task 4: Write YAML content files

**Files:**
- Create: `app/content/regionen/deutschland.yaml`
- Create: `app/content/regionen/brandenburg.yaml`
- Create: `app/content/regionen/berlin.yaml`

**Important:** All content must be factually accurate. Sources:
- Rote-Liste-Zentrum: species status "Ungefährdet", "deutliche Zunahme"
- Landeck et al. 2013: Brandenburg first record 2007, distribution data
- Kriegs et al. (LWL): two population corridors, active + passive spreading
- Naturschutzfonds Brandenburg: project launch November 2016
- NABU species portrait: biology facts
- Your own mantis-religiosa page: existing content for consistency

**Step 1: Create deutschland.yaml**

Write the file with ~500 words of unique editorial content about Mantis religiosa in Germany. Key angles:
- Two population corridors (western from France via Baden-Württemberg, eastern from Czech Republic via Brandenburg)
- Conservation status: "Ungefährdet" per Rote-Liste-Zentrum (previously Red-Listed, reclassified due to "deutliche Zunahme")
- Named "Insekt des Jahres 2017"
- Climate-driven northward spread
- Protected under BArtSchV as "besonders geschützt"

Sections: Verbreitung in Deutschland, Zwei Populationskorridore, Schutzstatus, Lebensräume, Gottesanbeterin melden

**Step 2: Create brandenburg.yaml**

Key angles:
- Core eastern population region
- Erstnachweis 2007 (Landeck et al. 2013)
- Citizen science project "Gottesanbeterin gesucht!" since November 2016
- Naturkundemuseum Potsdam + Mantidenfreunde Berlin-Brandenburg
- Southern Brandenburg focus, Bergbaufolgelandschaften as habitat
- Trockenwarme Habitate: Trockenrasen, Brachflächen, Gärten

Sections: Verbreitung in Brandenburg, Geschichte der Ausbreitung, Lebensräume in Brandenburg, So erkennen Sie die Gottesanbeterin, Sichtung melden

**Step 3: Create berlin.yaml**

Key angles:
- Urban mantis population connected to Brandenburg population
- Documented on Schöneberger Südgelände (urban nature park)
- Urban heat island effect aids survival
- Gardens, Hinterhöfe, Kleingärten, Brachflächen as habitat
- Growing number of sightings in recent years

Sections: Gottesanbeterin in der Großstadt, Verbreitung in Berlin, Urbane Lebensräume, Erkennung und Verwechslung, Sichtung melden

**Step 4: Run tests**

Run: `cd /Users/leon/Documents/projects/mantis/mantis && uv run pytest tests/functional/test_regionen.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add app/content/regionen/
git commit -m "content(regionen): add editorial content for Deutschland, Brandenburg, Berlin"
```

---

### Task 5: Humanize content

**REQUIRED SKILL:** Use the `humanizer` skill to review all 3 YAML content files.

**Files:**
- Modify: `app/content/regionen/deutschland.yaml`
- Modify: `app/content/regionen/brandenburg.yaml`
- Modify: `app/content/regionen/berlin.yaml`

**Step 1:** Run humanizer skill on each YAML file's German text content. Check for:
- Em dash overuse → use commas or restructure
- AI vocabulary (transformativ, bemerkenswert, etc.)
- Promotional language
- Rule of three patterns
- Overly formal or stiff phrasing

**Step 2:** Ensure the language reads naturally, as if written by a German nature enthusiast, not generated. Keep the factual accuracy intact.

**Step 3: Commit**

```bash
git add app/content/regionen/
git commit -m "style(regionen): humanize editorial content"
```

---

### Task 6: Update sitemap.xml

**Files:**
- Modify: `app/static/sitemap.xml`

**Step 1: Add regional pages to sitemap**

Add before the closing `</urlset>` tag:

```xml
  <url>
    <loc>https://gottesanbeterin-gesucht.de/gottesanbeterin-in-deutschland/</loc>
    <lastmod>2026-02-20T00:00:00+00:00</lastmod>
    <priority>0.80</priority>
  </url>
  <url>
    <loc>https://gottesanbeterin-gesucht.de/gottesanbeterin-in-brandenburg/</loc>
    <lastmod>2026-02-20T00:00:00+00:00</lastmod>
    <priority>0.80</priority>
  </url>
  <url>
    <loc>https://gottesanbeterin-gesucht.de/gottesanbeterin-in-berlin/</loc>
    <lastmod>2026-02-20T00:00:00+00:00</lastmod>
    <priority>0.80</priority>
  </url>
```

**Step 2: Commit**

```bash
git add app/static/sitemap.xml
git commit -m "seo(sitemap): add regional landing pages"
```

---

### Task 7: Add internal links from existing pages

**Files:**
- Modify: `app/templates/home.html` (add regional links section)
- Modify: `app/templates/mantis_religiosa.html` (add "Regionale Verbreitung" section)

**Step 1: Add links to homepage**

In `home.html`, find an appropriate location in the content flow (after the species info section) and add contextual links:

```html
<p class="prose-content-spaced">
    Erfahren Sie mehr über die Verbreitung der Gottesanbeterin in
    <a href="/gottesanbeterin-in-deutschland/" class="text-green-700 hover:underline">Deutschland</a>,
    <a href="/gottesanbeterin-in-brandenburg/" class="text-green-700 hover:underline">Brandenburg</a> und
    <a href="/gottesanbeterin-in-berlin/" class="text-green-700 hover:underline">Berlin</a>.
</p>
```

**Step 2: Add section to mantis_religiosa.html**

Before the closing `</div>` of the main content, add a "Regionale Verbreitung" section:

```html
<div class="mb-12">
    <h2 class="section-heading">Regionale Verbreitung</h2>
    <p class="prose-content-spaced">
        Die Europäische Gottesanbeterin breitet sich zunehmend in Deutschland aus.
        Erfahren Sie mehr über die Verbreitung in einzelnen Regionen:
    </p>
    <div class="grid grid-cols-1 gap-4 mt-4 md:grid-cols-3">
        <a href="/gottesanbeterin-in-deutschland/" class="block p-6 transition-shadow bg-white rounded-lg shadow-md hover:shadow-lg">
            <h3 class="text-lg font-semibold text-green-700">Deutschland</h3>
            <p class="mt-2 text-sm text-gray-600">Überblick über die Verbreitung in ganz Deutschland</p>
        </a>
        <a href="/gottesanbeterin-in-brandenburg/" class="block p-6 transition-shadow bg-white rounded-lg shadow-md hover:shadow-lg">
            <h3 class="text-lg font-semibold text-green-700">Brandenburg</h3>
            <p class="mt-2 text-sm text-gray-600">Kerngebiet der östlichen Population</p>
        </a>
        <a href="/gottesanbeterin-in-berlin/" class="block p-6 transition-shadow bg-white rounded-lg shadow-md hover:shadow-lg">
            <h3 class="text-lg font-semibold text-green-700">Berlin</h3>
            <p class="mt-2 text-sm text-gray-600">Urbane Verbreitung in der Hauptstadt</p>
        </a>
    </div>
</div>
```

**Step 3: Write a test for the internal links**

Add to `tests/functional/test_regionen.py`:

```python
def test_homepage_links_to_regional_pages(client):
    """Homepage contains links to regional pages."""
    response = client.get("/")
    assert b"gottesanbeterin-in-deutschland" in response.data


def test_mantis_page_links_to_regional_pages(client):
    """Mantis religiosa page contains links to regional pages."""
    response = client.get("/mantis-religiosa")
    assert b"gottesanbeterin-in-brandenburg" in response.data
```

**Step 4: Run all tests**

Run: `cd /Users/leon/Documents/projects/mantis/mantis && uv run pytest tests/functional/test_regionen.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add app/templates/home.html app/templates/mantis_religiosa.html tests/functional/test_regionen.py
git commit -m "seo(regionen): add internal links from homepage and mantis-religiosa page"
```

---

### Task 8: Final verification

**Step 1: Run the full test suite**

Run: `cd /Users/leon/Documents/projects/mantis/mantis && uv run pytest -v`
Expected: ALL PASS (no regressions)

**Step 2: Run ruff linter**

Run: `cd /Users/leon/Documents/projects/mantis/mantis && uv run ruff check app/routes/regionen.py`
Expected: No errors

**Step 3: Manual smoke test (if dev server available)**

Run: `cd /Users/leon/Documents/projects/mantis/mantis && uv run flask run`
Visit:
- `http://localhost:5000/gottesanbeterin-in-deutschland/`
- `http://localhost:5000/gottesanbeterin-in-brandenburg/`
- `http://localhost:5000/gottesanbeterin-in-berlin/`

Check: Page renders, breadcrumbs work, CTA links to /melden, sibling links work, no broken layout.

**Step 4: Verify SEO elements in HTML source**

For each page, check:
- `<title>` contains region name
- `<meta name="description">` is unique per page
- `<link rel="canonical">` is self-referencing
- OG and Twitter meta tags present
- JSON-LD Article schema present
- JSON-LD BreadcrumbList schema present

---

## Task Dependencies

```
Task 1 (PyYAML) → Task 2 (Blueprint) → Task 3 (Template) → Task 4 (Content) → Task 5 (Humanize) → Task 6 (Sitemap) → Task 7 (Internal Links) → Task 8 (Verification)
```

Tasks 6 and 7 can run in parallel after Task 5.
