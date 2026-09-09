"""Request-argument parsing and the shared reviewer/export query."""

from datetime import datetime

from flask import current_app, request
from sqlalchemy import false, func, select
from sqlalchemy.orm import contains_eager, joinedload

from app.tools.fts import prefix_tsquery
from app.database.models import (
    STATUS_FILTERS,
    TblFundorte,
    TblMeldungen,
    TblMeldungUser,
)


def _parse_german_date(value: str | None) -> datetime | None:
    """Parse a dd.mm.YYYY date string, returning None on empty/invalid input."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%d.%m.%Y")
    except ValueError:
        return None


def normalize_filter_status(value: str | None, default: str = "offen") -> str:
    """Normalise a status filter value.

    The value arrives either as a URL argument or in an HTMX form body, and
    both the SQL query and the per-card visibility check compare against it —
    so they have to agree on casing.
    """
    return (value or default).strip().lower()


def get_reviewer_filter_args():
    """Read the shared reviewer/export filter arguments from the request."""
    return {
        "filter_status": normalize_filter_status(request.args.get("statusInput")),
        "filter_type": request.args.get("typeInput"),
        "search_query": request.args.get("q"),
        "search_type": request.args.get("search_type", "full_text"),
        "date_from": request.args.get("dateFrom"),
        "date_to": request.args.get("dateTo"),
        "date_type": request.args.get("dateType", "fund"),
    }


def get_filtered_query(
    filter_status: str | None = None,
    filter_type: str | None = None,
    search_query: str | None = None,
    search_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    date_type: str | None = None,
):
    """Get filtered select statement based on parameters.

    Returns a single-entity select(TblMeldungen) with relationship-based JOINs
    and contains_eager() options. Compatible with db.paginate() and
    db.session.scalars().
    """
    # INNER JOINs to melduser/users intentionally exclude meldungen without a
    # reporter link (application invariant: every report has exactly one melduser).
    # contains_eager() populates relationships from these existing JOINs.
    # db.paginate() calls .unique() internally, so duplicate rows from the
    # melduser JOIN (if any) are deduplicated before pagination.
    stmt = (
        select(TblMeldungen)
        .join(TblMeldungen.fundort)
        .join(TblFundorte.location_type)
        .join(TblMeldungen.reporter_link)
        .join(TblMeldungUser.reporter)
        .options(
            contains_eager(TblMeldungen.fundort).contains_eager(
                TblFundorte.location_type
            ),
            contains_eager(TblMeldungen.reporter_link).contains_eager(
                TblMeldungUser.reporter
            ),
            # joinedload auto-aliases the users table to avoid conflict
            # with the reporter JOIN that already references users.
            joinedload(TblMeldungen.approver),
        )
    )

    # The hybrids compile to array containment: statuses @> ARRAY['VALUE'].
    if filter_status in STATUS_FILTERS:
        stmt = stmt.where(getattr(TblMeldungen, STATUS_FILTERS[filter_status]))
    elif filter_status == "all" or search_query:
        # "all" asks for everything; a search query stands on its own.
        pass
    else:
        stmt = stmt.where(~TblMeldungen.is_deleted)

    # Apply type filter
    if filter_type:
        if filter_type == "maennlich":
            stmt = stmt.where(TblMeldungen.art_m >= 1)
        elif filter_type == "weiblich":
            stmt = stmt.where(TblMeldungen.art_w >= 1)
        elif filter_type == "oothek":
            stmt = stmt.where(TblMeldungen.art_o >= 1)
        elif filter_type == "Nymphe":
            stmt = stmt.where(TblMeldungen.art_n >= 1)
        elif filter_type == "andere":
            stmt = stmt.where(TblMeldungen.art_f >= 1)
        elif filter_type == "nicht_bestimmt":
            stmt = stmt.where(
                TblMeldungen.art_m.is_(None),
                TblMeldungen.art_w.is_(None),
                TblMeldungen.art_o.is_(None),
                TblMeldungen.art_n.is_(None),
                TblMeldungen.art_f.is_(None),
            )

    # Apply search
    if search_query:
        try:
            if search_type == "id":
                try:
                    search_id = int(search_query)
                    stmt = stmt.where(TblMeldungen.id == search_id)
                except ValueError:
                    search_type = "full_text"

            if search_type == "full_text":
                tsquery_text = prefix_tsquery(search_query)
                if tsquery_text is None:
                    # Nothing searchable in the input, so nothing matches.
                    stmt = stmt.where(false())
                else:
                    ts_query = func.to_tsquery("german", tsquery_text)
                    stmt = stmt.where(TblMeldungen.search_vector.op("@@")(ts_query))
                    stmt = stmt.order_by(
                        func.ts_rank_cd(TblMeldungen.search_vector, ts_query).desc()
                    )
        except Exception as e:
            current_app.logger.error(f"Search error: {e}")
            stmt = stmt.where(false())

    # Apply date filters
    # Choose which date column to filter on based on date_type
    date_column = (
        TblMeldungen.dat_meld if date_type == "meld" else TblMeldungen.dat_fund_von
    )

    parsed_from = _parse_german_date(date_from)
    parsed_to = _parse_german_date(date_to)

    if (date_from and parsed_from is None) or (date_to and parsed_to is None):
        current_app.logger.error(f"Date parsing error: {date_from!r} / {date_to!r}")
        stmt = stmt.where(false())
    elif parsed_from and parsed_to:
        stmt = stmt.where(date_column.between(parsed_from, parsed_to))
    elif parsed_from:
        stmt = stmt.where(date_column >= parsed_from)
    elif parsed_to:
        stmt = stmt.where(date_column <= parsed_to)

    return stmt
