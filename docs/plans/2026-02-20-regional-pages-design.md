# Regional Landing Pages Design

**Date**: 2026-02-20
**Status**: Approved
**Scope**: 3 pages (Deutschland, Brandenburg, Berlin) — expandable to Landkreise later

## Goal

Create static editorial landing pages for regional SEO targeting searches like "Gottesanbeterin Brandenburg", "Gottesanbeterin in Berlin melden", "Gottesanbeterin Deutschland Verbreitung". No German citizen science project currently does regional SEO for species pages — this is an untapped opportunity.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Page depth | 3 Bundesland/Land pages (expand to Landkreise later) | Start focused, prove concept |
| Data source | Static editorial only | No DB queries, pure content quality |
| URL structure | Flat keyword-rich: `/gottesanbeterin-in-<slug>/` | Matches search queries, proven for <100 pages |
| Content storage | YAML files + single Jinja2 template | Separation of content and design, git-diffable |
| Content authoring | Drafted from verified sources, reviewed before publishing | Factual accuracy is critical |

## URL Inventory

| URL | Type | Parent |
|-----|------|--------|
| `/gottesanbeterin-in-deutschland/` | land | — |
| `/gottesanbeterin-in-brandenburg/` | bundesland | deutschland |
| `/gottesanbeterin-in-berlin/` | bundesland | deutschland |

## File Structure

```
app/
  content/
    regionen/
      deutschland.yaml
      brandenburg.yaml
      berlin.yaml
  templates/
    region.html
  routes/
    regionen.py          # new Flask Blueprint
```

## YAML Schema

```yaml
slug: string             # URL slug (e.g., "brandenburg")
name: string             # Display name (e.g., "Brandenburg")
type: enum               # land | bundesland | landkreis | bezirk
parent: string|null      # Parent slug (null for deutschland)
title: string            # Page H1 and <title> prefix
meta_description: string # 150-160 chars
og_title: string         # OG title (can differ from page title)

intro: string            # Opening paragraph (~100 words)

sections:                # Content sections
  - heading: string      # H2 heading
    content: string      # Prose content (supports basic HTML for links)

children: list[string]   # Slugs of child pages (for future expansion)
siblings: list[string]   # Slugs of sibling pages
cta_text: string         # Call-to-action button text
cta_url: string          # CTA link target (typically /melden)
```

## Route Implementation

- New Blueprint `regionen` registered at app level
- Single route: `GET /gottesanbeterin-in-<slug>/`
- Loads `app/content/regionen/{slug}.yaml` via `safe_load`
- Returns 404 if YAML file not found
- Renders `region.html` with content dict

## Template Structure (region.html)

1. Breadcrumbs (BreadcrumbList JSON-LD)
2. H1 from `title`
3. Intro paragraph
4. Content sections (H2 + prose, using existing CSS classes)
5. CTA block (green button to /melden)
6. Related pages (siblings + children)
7. Cross-links to /mantis-religiosa, /bestimmung, /faq

SEO blocks override layout.html defaults:
- `{% block page_title %}`, `{% block meta_description %}`, `{% block canonical %}`
- `{% block og_meta %}`, `{% block twitter_meta %}`

Schema markup: WebPage + BreadcrumbList + Article (JSON-LD)

## Content Strategy

| Page | Key angles | Sources |
|------|-----------|---------|
| Deutschland | Two population corridors (west/east), Rote-Liste status "Ungefaehrdet", Insekt des Jahres 2017, climate-driven spread | Rote-Liste-Zentrum, Kriegs et al. (LWL), NABU |
| Brandenburg | Erstnachweis 2007, project since Nov 2016, southern BB focus, Bergbaufolgelandschaften | Landeck et al. 2013, Naturschutzfonds BB |
| Berlin | Urban sightings, Schöneberger Südgelände, heat island effect, gardens | iNaturalist, Berliner Zeitung |

Each page: ~500 words unique editorial, 5 sections (intro, Verbreitung, Lebensräume, Erkennung, Melden).

## Internal Linking

- Homepage: add links to regional pages in content flow
- /mantis-religiosa: add "Regionale Verbreitung" section
- Regional pages: cross-link siblings, link to /melden, /bestimmung, /mantis-religiosa
- sitemap.xml: add all 3 URLs with priority 0.80

## Future Expansion

When ready, add Landkreis pages by:
1. Creating new YAML files (e.g., `barnim.yaml`)
2. Setting `type: landkreis`, `parent: brandenburg`
3. Adding slug to parent's `children` list
4. Adding URL to sitemap.xml

No code changes needed — the template and route handle all region types.
