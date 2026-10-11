"""Count edits shared by the reviewer modal and data grid."""

from app.database.models import TblMeldungen

SPECIMEN_FIELDS = ("art_m", "art_w", "art_n", "art_o", "art_f")
COUNT_FIELDS = (*SPECIMEN_FIELDS, "tiere")
INT32_MAX = 2**31 - 1


def set_count(report: TblMeldungen, field: str, raw_value: str) -> None:
    """Set a count on a locked report; category edits also update its total."""
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError("Enter a whole number.") from exc
    if value < 0:
        raise ValueError("Count must be non-negative")
    if value > INT32_MAX:
        raise ValueError("Count value out of range")

    total = value
    if field != "tiere":
        total += sum(
            getattr(report, name) or 0 for name in SPECIMEN_FIELDS if name != field
        )
    if total > INT32_MAX:
        raise ValueError("Total count exceeds 2147483647.")
    setattr(report, field, value)
    report.tiere = total
