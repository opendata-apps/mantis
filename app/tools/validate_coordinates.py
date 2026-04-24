"""
Offline coordinate-vs-address plausibility checker.

Compares the address fields a user typed (ort, land) against what the
GemeindeFinder resolves from their map coordinates.  Catches the common
case of users placing a pin in the wrong city or state.

No external API calls — all lookups use the in-memory STRtree spatial index.
"""

from dataclasses import dataclass
from enum import Enum


class Issue(str, Enum):
    """Types of coordinate-address mismatches."""

    LAND_MISMATCH = "LAND_MISMATCH"
    ORT_MISMATCH = "ORT_MISMATCH"
    OUTSIDE_DE = "OUTSIDE_DE"


@dataclass(frozen=True, slots=True)
class Mismatch:
    """A single validation finding for one Fundort."""

    fundort_id: int
    issue: Issue
    stored_land: str
    expected_land: str
    stored_ort: str
    expected_ort: str


def names_match(stored: str, resolved: str) -> bool:
    """Case-insensitive substring containment in both directions.

    >>> names_match("Berlin-Mitte", "Berlin")
    True
    >>> names_match("Frankfurt", "Frankfurt am Main")
    True
    >>> names_match("München", "Hamburg")
    False
    """
    a = stored.lower().strip()
    b = resolved.lower().strip()
    if not a or not b:
        return False
    return a in b or b in a


def validate_fundorte(fundorte, get_spatial):
    """Check address fields against spatial lookup for a list of Fundorte.

    Args:
        fundorte: iterable of objects with .id, .latitude, .longitude, .ort, .land
        get_spatial: callable (lon, lat) -> dict with keys {land, gen} or None
                     (typically gemeinde_finder.get_amt_enriched)

    Returns:
        tuple of (mismatches: list[Mismatch], checked: int, skipped: int)
    """
    mismatches = []
    checked = 0
    skipped = 0

    for f in fundorte:
        # Parse coordinates
        try:
            lat = float(str(f.latitude).strip())
            lon = float(str(f.longitude).strip())
        except (ValueError, TypeError, AttributeError):
            skipped += 1
            continue

        checked += 1
        spatial = get_spatial((lon, lat))

        if spatial is None:
            mismatches.append(
                Mismatch(
                    fundort_id=f.id,
                    issue=Issue.OUTSIDE_DE,
                    stored_land=f.land or "",
                    expected_land="—",
                    stored_ort=f.ort or "",
                    expected_ort="—",
                )
            )
            continue

        expected_land = spatial["land"]
        expected_ort = spatial["gen"]
        stored_land = f.land or ""
        stored_ort = f.ort or ""

        # Land (Bundesland) check — exact case-insensitive match
        if stored_land and expected_land:
            if stored_land.strip().lower() != expected_land.strip().lower():
                mismatches.append(
                    Mismatch(
                        fundort_id=f.id,
                        issue=Issue.LAND_MISMATCH,
                        stored_land=stored_land,
                        expected_land=expected_land,
                        stored_ort=stored_ort,
                        expected_ort=expected_ort,
                    )
                )
                continue  # Land wrong → skip Ort check (redundant)

        # Ort (city/municipality) check — substring containment
        if stored_ort and expected_ort:
            if not names_match(stored_ort, expected_ort):
                mismatches.append(
                    Mismatch(
                        fundort_id=f.id,
                        issue=Issue.ORT_MISMATCH,
                        stored_land=stored_land,
                        expected_land=expected_land,
                        stored_ort=stored_ort,
                        expected_ort=expected_ort,
                    )
                )

    return mismatches, checked, skipped


def format_report(mismatches, checked, skipped):
    """Format validation results as a human-readable report string."""
    lines = []
    lines.append("")
    lines.append("Coordinate Validation Report")
    lines.append("=" * 70)
    lines.append(
        f"Checked: {checked}  |  Skipped: {skipped} (no coords)"
        f"  |  Mismatches: {len(mismatches)}"
    )
    lines.append("")

    if not mismatches:
        lines.append("No mismatches found.")
        return "\n".join(lines)

    # Table header
    hdr = (
        f"{'ID':>6}  {'Issue':<15} {'Stored Land':<20} {'Expected Land':<20}"
        f" {'Stored Ort':<20} {'Expected Ort':<20}"
    )
    lines.append(hdr)
    lines.append("-" * len(hdr))

    for m in mismatches:
        lines.append(
            f"{m.fundort_id:>6}  {m.issue.value:<15}"
            f" {m.stored_land:<20} {m.expected_land:<20}"
            f" {m.stored_ort:<20} {m.expected_ort:<20}"
        )

    return "\n".join(lines)


def format_csv(mismatches):
    """Format validation results as CSV lines (including header)."""
    lines = ["id,issue,stored_land,expected_land,stored_ort,expected_ort"]
    for m in mismatches:
        # Escape fields that might contain commas
        fields = [
            str(m.fundort_id),
            m.issue.value,
            f'"{m.stored_land}"',
            f'"{m.expected_land}"',
            f'"{m.stored_ort}"',
            f'"{m.expected_ort}"',
        ]
        lines.append(",".join(fields))
    return "\n".join(lines)
