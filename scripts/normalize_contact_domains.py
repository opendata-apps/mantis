#!/usr/bin/env python
"""One-off repair: lowercase the domain of stored reporter addresses.

Every report writes a new users row, so a repeat reporter accumulates one row
per report. Two rows differing only in domain case are the same mailbox but
never compare equal, which splits what a reviewer sees as one person — the
report count in the admin modal is the exact-match consumer left. Newer rows
are already normalised on write; this brings the older ones to the same form
with the same validator.

Not an access repair: reading a report is granted by the melduser link, never
by a matching contact string (see provider.py).

    python scripts/normalize_contact_domains.py            # report only
    python scripts/normalize_contact_domains.py --apply    # write
"""

import sys

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import select

from app import create_app
from app.extensions import db
from app.database.users import TblUsers


def main(apply_changes):
    changed = skipped = 0

    for user in db.session.scalars(
        select(TblUsers).where(TblUsers.user_kontakt != "").order_by(TblUsers.id)
    ):
        contact = user.user_kontakt
        if not contact:
            continue
        try:
            # The call _create_user() makes, so repaired rows land on exactly
            # the form new rows get. allow_smtputf8=False mirrors the form.
            normalized = validate_email(
                contact, check_deliverability=False, allow_smtputf8=False
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
