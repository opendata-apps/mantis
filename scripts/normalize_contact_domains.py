#!/usr/bin/env python
"""One-off repair: lowercase the domain of stored reporter addresses.

Every report writes a new users row, so a repeat reporter accumulates one row
per report. provider.py matches reporter to reports by exact user_kontakt
comparison, so two rows differing only in domain case split one reporter's
history: reports drop out of "Meine Sichtungen" and their own photos answer 403.
Addresses have been normalised on write since 2026-08-18; this brings the older
rows to the same form by calling the same validator.

    python scripts/normalize_contact_domains.py            # report only
    python scripts/normalize_contact_domains.py --apply    # write
"""

import sys

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import select

from app import create_app, db
from app.database.users import TblUsers


def main(apply_changes):
    changed = skipped = 0

    for user in db.session.scalars(
        select(TblUsers).where(TblUsers.user_kontakt != "").order_by(TblUsers.id)
    ):
        try:
            # The call _create_user() makes, so repaired rows land on exactly
            # the form new rows get. allow_smtputf8=False mirrors the report
            # form; without it an umlaut before the @ passes here but yields
            # ascii_email=None at send time, leaving the row undeliverable.
            normalized = validate_email(
                user.user_kontakt, check_deliverability=False, allow_smtputf8=False
            ).normalized
        except EmailNotValidError as err:
            print(f"skip id={user.id} {user.user_kontakt!r}: {err}")
            skipped += 1
            continue

        if normalized != user.user_kontakt:
            print(f"id={user.id} {user.user_kontakt!r} -> {normalized!r}")
            changed += 1
            if apply_changes:
                user.user_kontakt = normalized

    if apply_changes:
        db.session.commit()
        print(f"\nNormalized {changed}, skipped {skipped}.")
    else:
        print(f"\nWould normalize {changed}, skip {skipped}. Re-run with --apply.")


if __name__ == "__main__":
    with create_app().app_context():
        main("--apply" in sys.argv)
