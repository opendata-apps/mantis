# Geo-Grade: coordinate/address quality grading for sightings

## Problem

Each sighting stores user-supplied address fields (`ort`, `land`, `kreis`) alongside
map coordinates. The coordinates are trustworthy (the reporter drops a pin); the
typed text is noisy. The existing `validate-coordinates` command flags 5,189 of
28,847 records, but **4,922 (95%) are false positives**: the typed `ort` is a
sub-municipal locality (Ortsteil, e.g. "Schadewitz") while the spatial finder
resolves only to the Gemeinde level (`gen`, e.g. "Schönborn"). The reference data
(`ags_gemeinden.json`, BKG VG250) stops at the Gemeinde level, so the check cannot
tell a wrong pin from a correctly-pinned village whose name differs from its
municipality.

Goal: a per-sighting **confidence grade** that routes questionable records
into the reviewer queue and leaves correct records unflagged. The grade never
mutates data — a human confirms or fixes flagged records.

## Evidence basis

- **GN250 (Geographische Namen 1:250 000, BKG)** provides ~170,000 named-place
  points including Gemeindeteile/Ortslagen, each carrying the administrative key
  (AGS), Kreis, and Verwaltungsgemeinschaft. Served via the same WFS pattern the
  project already uses for VG250: `wfs_gn250_inspire`, FeatureType `gn:NamedPlace`,
  settlement type `populatedPlace` (finer class in `gn:localType`). Same provider
  and licence (Datenlizenz Deutschland Namensnennung 2.0). Verified live: a bbox
  query returns the village-level names typed into `ort` (e.g. `Friedersdorf`,
  `Rückersdorf`, `Lindena`), confirming the layer bridges the Ortsteil↔Gemeinde gap.
- **Confidence model** follows reverse-geocoding industry practice: match at the
  finest administrative level the coordinate corroborates ("UpHierarchy", Azure
  Maps) and weight by distance to the nearest named place (Pelias/Stadia buckets).

## Architecture

Five units, each independently testable:

1. **`geo_names` table** + **`flask seed-gn250`** — one-time WFS ingestion.
2. **`app/tools/geo_names.py`** — loads `geo_names` into a shapely STRtree for
   nearest-neighbour lookup (sibling of `gemeinde_finder.py`).
3. **`app/tools/geo_grade.py`** — pure grading function over injected lookups.
4. **`fundorte` grade columns** + Alembic migration; computed at submission, on
   coordinate edit, and via **`flask grade-fundorte`** backfill.
5. **Reviewer surfacing** — confidence badge on the report card + a "low
   confidence" filter wired into the existing reviewer filter.

## Data model

`geo_names` (new table):

| column | type | note |
|---|---|---|
| `id` | int identity PK | |
| `name` | text | place name as published |
| `name_norm` | text | lower/trim/umlaut-folded, indexed for matching |
| `ags` | bigint | administrative key linking to Gemeinde |
| `kreis` | text | |
| `longitude` | double | |
| `latitude` | double | |

`fundorte` additions:

| column | type | note |
|---|---|---|
| `geo_grade` | text | `HIGH` \| `MEDIUM` \| `LOW` \| `UNKNOWN` |
| `geo_confidence` | double | 0.0–1.0 |
| `geo_matched_level` | text | `ORTSTEIL` \| `GEMEINDE` \| `KREIS` \| `LAND` \| `OUTSIDE_DE` \| `NONE` |
| `geo_reasons` | jsonb | list of human-readable strings |
| `geo_graded_at` | timestamptz | nullable; set when graded |

## Grade algorithm — `geo_grade.grade_location`

Pure function: `grade_location(lat, lon, stored_land, stored_kreis, stored_ort, find_amt, nearest_place) -> GeoGrade`,
where `find_amt` is `gemeinde_finder.get_amt_enriched` and `nearest_place` is
`geo_names`' nearest-neighbour callable. Both are injected so the grader is tested
without I/O.

1. `resolved = find_amt((lon, lat))`.
2. `resolved is None` → `OUTSIDE_DE`, grade `LOW`, confidence `0.10`.
3. `land_match = norm(stored_land) == norm(resolved.land)`;
   `kreis_match = norm(stored_kreis) == norm(resolved.kreis)` (when stored).
4. `place, dist_m = nearest_place((lon, lat))`.
5. Pick `matched_level` (first that holds):
   - `ORTSTEIL` — `names_match(stored_ort, place.name)` and `dist_m <= 2000`.
   - `GEMEINDE` — `names_match(stored_ort, resolved.gen)` or `place.ags == resolved.ags`.
   - `KREIS` — `land_match and kreis_match`.
   - `LAND` — `land_match`.
   - `NONE` — otherwise.
6. `confidence` = base-per-level (`ORTSTEIL .95`, `GEMEINDE .90`, `KREIS .60`,
   `LAND .35`, `NONE .15`, `OUTSIDE_DE .10`) reduced by a distance penalty when
   `dist_m` is large.
7. `grade` = `HIGH` if level in {`ORTSTEIL`, `GEMEINDE`}; `MEDIUM` if `KREIS`;
   else `LOW`.
8. `reasons` — e.g. `["Land matches", "nearest place 'Schadewitz' 140 m"]`.

`names_match` reuses the existing bidirectional case-insensitive substring helper
from `app/tools/validate_coordinates.py`, extended with umlaut folding.

This dissolves the false positives: "Schadewitz" is a GN250 populated place at the
pin → `ORTSTEIL` → `HIGH`, unflagged. A pin dropped in the wrong Kreis still falls
to `LAND`/`NONE` → `LOW`, flagged.

## Integration

- **Submission** (`report.py`): after `calculate_spatial_fields`, compute the grade
  and set the columns before commit. Grading is enrichment, not boundary
  validation — a grading exception leaves the report committed, the columns set to
  `UNKNOWN`, and the error logged.
- **Coordinate/address edit** (`admin.change_mantis_meta_data`, fields
  `latitude`/`longitude`/`ort`/`land`): recompute the grade for that Fundort.
- **Backfill** (`flask grade-fundorte [--only-ungraded]`): idempotent batch grade
  of existing rows, streamed with `yield_per`.

## Reviewer surfacing

- A badge macro on the report card: green/amber/red dot for HIGH/MEDIUM/LOW with a
  tooltip listing `geo_reasons`.
- A reviewer filter option "niedrige Konfidenz" → `where geo_grade == 'LOW'`,
  added to the existing reviewer filter (`get_filtered_query`), plus sort by
  `geo_confidence` ascending. Reuses the established filter-dispatch pattern.

## Error handling

- `seed-gn250` WFS failure → abort loudly via `click.Abort` (matches `seed-ags`);
  no silent fallback to stale data.
- If the `geo_names` index is unavailable at grade time, the grade is computed from
  the Gemeinde lookup alone, `matched_level` capped at `KREIS`, with an explicit
  `geonames_unavailable` reason. It is never silently `HIGH`.
- Grading never blocks a submission (see Integration).

## Testing

- **`geo_grade` unit tests** with a stub `find_amt` and a synthetic nearest-place
  callable, covering each level: `OUTSIDE_DE`, Land-mismatch → `LOW`, Kreis-only →
  `MEDIUM`, Gemeinde match → `HIGH`, **Ortsteil match (Schadewitz regression) →
  `HIGH`**, and missing `ort`.
- **Ingestion test**: a mocked WFS payload → parse, filter to `populatedPlace`,
  normalize → expected `geo_names` rows (non-settlement features dropped).
- **Backfill command test**: grades the seeded Fundorte; second run is a no-op with
  `--only-ungraded`.

## Out of scope (YAGNI)

- Auto-correcting or normalizing the stored address fields.
- Submission-time gating/blocking of low-confidence pins.
- Automatic re-grading when GN250 is updated (operator re-runs `seed-gn250` then
  `grade-fundorte`).

## Rollout

1. Alembic migration: `geo_names` table + `fundorte` columns.
2. `flask seed-gn250` on prod (fetch + store; JSON fallback committed for offline
   seeding, like `ags_gemeinden.json`).
3. `flask grade-fundorte` backfill of the 28k existing rows.
4. Enable the reviewer badge + low-confidence filter.
