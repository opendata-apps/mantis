"""collapse the fts search_vector expression to one definition

The weighted document was written out four times: twice inside
recompute_search_vector() (one branch per fo_zuordnung IS NULL), once inline in
the meldungen BEFORE trigger, and once in the backfill of a90f81bfa252. The
copies had already drifted apart, and two of them are wrong:

* The backfill inner-joined fundorte, so every meldung without a fundort kept
  search_vector = NULL and never matched a search.
* The trigger read its fundort and melder values with SELECT ... INTO. Without
  STRICT that assigns NULL to every target when no row is found, so the
  `text := ''` defaults never survive. A meldung with no melduser row
  therefore got to_tsvector('german', NULL) -> NULL, and NULL swallows the
  whole `||` chain: the entire document became NULL.
  https://www.postgresql.org/docs/16/plpgsql-statements.html (43.5.3)

Both disappear once there is a single definition. meldung_search_vector() takes
the meldungen values that a BEFORE trigger only has in NEW, looks the joined
rows up itself, and uses concat_ws so a missing join contributes nothing
instead of nulling the document. The trigger, the recompute function and the
backfill repair all call it.

The fundorte/beschreibung/users triggers also stop looping. Each used to walk
its affected meldungen with FOR ... LOOP PERFORM recompute_search_vector(id),
which issues one UPDATE per row; editing "Im Garten" ran 8141 of them. One
set-based UPDATE does the same work and is what the trigger body was
expressing anyway. Measured on a production copy that edit goes from ~1.6 s to
~1.3 s -- the cost is dominated by evaluating the vector and writing the GIN
entries, not by the loop, so this is a readability change that happens to be
slightly faster, not a performance fix.

The contact address now enters the document twice: once whole and once with
the '@' replaced by a space. The default parser treats an address as a single
token, so 'anna@gmx.de' indexed only as 'anna@gmx.de' -- searching gmx.de
matched 3 reports while 4329 reporters actually use that domain. Keeping the
whole address as well means the exact-address search that reviewers already
rely on keeps working.

Note concat_ws is STABLE, not IMMUTABLE, so none of this can become a stored
generated column -- and a generated column could not reach the joined tables
anyway: the expression "cannot use subqueries or reference anything other than
the current row". The triggers are the price of a document that spans
meldungen, fundorte, beschreibung, melduser and users.
https://www.postgresql.org/docs/16/ddl-generated-columns.html (5.3)

Revision ID: d4e5f6a7b8c9
Revises: 1eb277e10893
Create Date: 2026-09-08 23:40:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "d4e5f6a7b8c9"
down_revision = "1eb277e10893"
branch_labels = None
depends_on = None


# The one definition of the document. Anchored on a one-row subselect so the
# LEFT JOINs always have a driving row, which is what lets a meldung without a
# fundort or without a melduser still produce a vector. uq_melduser_id_meldung
# already limits the melduser join to one row; LIMIT 1 only keeps the function
# scalar if that constraint is ever dropped.
SEARCH_VECTOR_FUNCTION = """
CREATE OR REPLACE FUNCTION meldung_search_vector(
    p_meldung_id integer,
    p_fo_zuordnung integer,
    p_bearb_id text,
    p_anm_melder text,
    p_anm_bearbeiter text
) RETURNS tsvector AS $$
    SELECT setweight(to_tsvector('german',
               concat_ws(' ', f.ort, f.kreis, f.land, f.plz)), 'A')
        || setweight(to_tsvector('german',
               concat_ws(' ', u.user_name, u.user_kontakt,
                         replace(u.user_kontakt, '@', ' '), u.user_id, p_bearb_id)), 'B')
        || setweight(to_tsvector('german',
               concat_ws(' ', f.strasse, f.amt, f.mtb, b.beschreibung)), 'C')
        || setweight(to_tsvector('german',
               concat_ws(' ', p_anm_melder, p_anm_bearbeiter)), 'D')
    FROM (SELECT 1) AS anchor
    LEFT JOIN fundorte f ON f.id = p_fo_zuordnung
    LEFT JOIN beschreibung b ON b.id = f.beschreibung
    LEFT JOIN melduser mu ON mu.id_meldung = p_meldung_id
    LEFT JOIN users u ON u.id = mu.id_user
    LIMIT 1;
$$ LANGUAGE sql STABLE;
"""

# Stays a BEFORE trigger: assigning NEW directly avoids a second write per
# INSERT, and routing it through the shared function costs ~0.02 ms per row.
TRIGGER_MELDUNGEN = """
CREATE OR REPLACE FUNCTION trg_meldungen_search_vector()
RETURNS trigger AS $$
BEGIN
    NEW.search_vector := meldung_search_vector(
        NEW.id, NEW.fo_zuordnung, NEW.bearb_id, NEW.anm_melder, NEW.anm_bearbeiter);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

# The fundorte/beschreibung/melduser/users triggers call this unchanged; only
# its body collapses from two near-identical UPDATE branches to one.
RECOMPUTE_FUNCTION = """
CREATE OR REPLACE FUNCTION recompute_search_vector(target_id integer)
RETURNS void AS $$
BEGIN
    UPDATE meldungen m
    SET search_vector = meldung_search_vector(
        m.id, m.fo_zuordnung, m.bearb_id, m.anm_melder, m.anm_bearbeiter)
    WHERE m.id = target_id;
END;
$$ LANGUAGE plpgsql;
"""

# The three fan-out triggers. Each selects the meldungen its own table feeds
# into and rewrites their vectors in one statement. SET touches only
# search_vector, which is not in the meldungen trigger's UPDATE OF list, so
# this does not re-fire trg_meldungen_search_vector().
TRIGGER_FUNDORTE = """
CREATE OR REPLACE FUNCTION trg_fundorte_search_vector()
RETURNS trigger AS $$
BEGIN
    UPDATE meldungen m
    SET search_vector = meldung_search_vector(
        m.id, m.fo_zuordnung, m.bearb_id, m.anm_melder, m.anm_bearbeiter)
    WHERE m.fo_zuordnung = NEW.id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

TRIGGER_BESCHREIBUNG = """
CREATE OR REPLACE FUNCTION trg_beschreibung_search_vector()
RETURNS trigger AS $$
BEGIN
    UPDATE meldungen m
    SET search_vector = meldung_search_vector(
        m.id, m.fo_zuordnung, m.bearb_id, m.anm_melder, m.anm_bearbeiter)
    FROM fundorte f
    WHERE f.id = m.fo_zuordnung AND f.beschreibung = NEW.id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

TRIGGER_USERS = """
CREATE OR REPLACE FUNCTION trg_users_search_vector()
RETURNS trigger AS $$
BEGIN
    UPDATE meldungen m
    SET search_vector = meldung_search_vector(
        m.id, m.fo_zuordnung, m.bearb_id, m.anm_melder, m.anm_bearbeiter)
    FROM melduser mu
    WHERE mu.id_meldung = m.id AND mu.id_user = NEW.id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

# Every row, not just the ones a90f81bfa252 skipped: splitting the contact
# address changes the document for each meldung that has one. Writing only the
# rows that actually differ keeps the GIN churn down; on a production copy this
# rewrites all 28915 rows in ~6 s.
REPAIR_BACKFILL = """
UPDATE meldungen m
SET search_vector = meldung_search_vector(
    m.id, m.fo_zuordnung, m.bearb_id, m.anm_melder, m.anm_bearbeiter)
WHERE m.search_vector IS DISTINCT FROM meldung_search_vector(
    m.id, m.fo_zuordnung, m.bearb_id, m.anm_melder, m.anm_bearbeiter);
"""

# --- previous definitions, restored on downgrade ---

OLD_TRIGGER_MELDUNGEN = """
CREATE OR REPLACE FUNCTION trg_meldungen_search_vector()
RETURNS trigger AS $$
DECLARE
    f_ort text := '';
    f_kreis text := '';
    f_land text := '';
    f_plz text := '';
    f_strasse text := '';
    f_amt text := '';
    f_mtb text := '';
    f_beschreibung text := '';
    u_name text := '';
    u_kontakt text := '';
    u_uid text := '';
BEGIN
    IF NEW.fo_zuordnung IS NOT NULL THEN
        SELECT
            coalesce(f.ort, ''), coalesce(f.kreis, ''), coalesce(f.land, ''),
            coalesce(cast(f.plz as text), ''),
            coalesce(f.strasse, ''), coalesce(f.amt, ''), coalesce(f.mtb, ''),
            coalesce(b.beschreibung, '')
        INTO f_ort, f_kreis, f_land, f_plz, f_strasse, f_amt, f_mtb, f_beschreibung
        FROM fundorte f
        LEFT JOIN beschreibung b ON f.beschreibung = b.id
        WHERE f.id = NEW.fo_zuordnung;
    END IF;

    SELECT coalesce(u.user_name, ''), coalesce(u.user_kontakt, ''), coalesce(u.user_id, '')
    INTO u_name, u_kontakt, u_uid
    FROM melduser mu
    JOIN users u ON mu.id_user = u.id
    WHERE mu.id_meldung = NEW.id
    LIMIT 1;

    NEW.search_vector :=
        setweight(to_tsvector('german',
            f_ort || ' ' || f_kreis || ' ' || f_land || ' ' || f_plz
        ), 'A') ||
        setweight(to_tsvector('german',
            u_name || ' ' || u_kontakt || ' ' || u_uid || ' ' || coalesce(NEW.bearb_id, '')
        ), 'B') ||
        setweight(to_tsvector('german',
            f_strasse || ' ' || f_amt || ' ' || f_mtb || ' ' || f_beschreibung
        ), 'C') ||
        setweight(to_tsvector('german',
            coalesce(NEW.anm_melder, '') || ' ' || coalesce(NEW.anm_bearbeiter, '')
        ), 'D');

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

OLD_TRIGGER_FUNDORTE = """
CREATE OR REPLACE FUNCTION trg_fundorte_search_vector()
RETURNS trigger AS $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN SELECT id FROM meldungen WHERE fo_zuordnung = NEW.id LOOP
        PERFORM recompute_search_vector(r.id);
    END LOOP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

OLD_TRIGGER_BESCHREIBUNG = """
CREATE OR REPLACE FUNCTION trg_beschreibung_search_vector()
RETURNS trigger AS $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT m.id FROM meldungen m
        JOIN fundorte f ON m.fo_zuordnung = f.id
        WHERE f.beschreibung = NEW.id
    LOOP
        PERFORM recompute_search_vector(r.id);
    END LOOP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

OLD_TRIGGER_USERS = """
CREATE OR REPLACE FUNCTION trg_users_search_vector()
RETURNS trigger AS $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN SELECT id_meldung FROM melduser WHERE id_user = NEW.id LOOP
        PERFORM recompute_search_vector(r.id_meldung);
    END LOOP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

OLD_RECOMPUTE_FUNCTION = """
CREATE OR REPLACE FUNCTION recompute_search_vector(target_id integer)
RETURNS void AS $$
BEGIN
    UPDATE meldungen m
    SET search_vector = sub.sv
    FROM (
        SELECT m2.id,
            setweight(to_tsvector('german',
                coalesce(f.ort, '') || ' ' || coalesce(f.kreis, '') || ' ' ||
                coalesce(f.land, '') || ' ' || coalesce(cast(f.plz as text), '')
            ), 'A') ||
            setweight(to_tsvector('german',
                coalesce(u.user_name, '') || ' ' || coalesce(u.user_kontakt, '') || ' ' ||
                coalesce(u.user_id, '') || ' ' || coalesce(m2.bearb_id, '')
            ), 'B') ||
            setweight(to_tsvector('german',
                coalesce(f.strasse, '') || ' ' || coalesce(f.amt, '') || ' ' ||
                coalesce(f.mtb, '') || ' ' || coalesce(b.beschreibung, '')
            ), 'C') ||
            setweight(to_tsvector('german',
                coalesce(m2.anm_melder, '') || ' ' || coalesce(m2.anm_bearbeiter, '')
            ), 'D') AS sv
        FROM meldungen m2
        JOIN fundorte f ON m2.fo_zuordnung = f.id
        LEFT JOIN beschreibung b ON f.beschreibung = b.id
        LEFT JOIN melduser mu ON m2.id = mu.id_meldung
        LEFT JOIN users u ON mu.id_user = u.id
        WHERE m2.id = target_id
    ) sub
    WHERE m.id = sub.id;

    UPDATE meldungen m
    SET search_vector = sub.sv
    FROM (
        SELECT m2.id,
            setweight(to_tsvector('german',
                coalesce(u.user_name, '') || ' ' || coalesce(u.user_kontakt, '') || ' ' ||
                coalesce(u.user_id, '') || ' ' || coalesce(m2.bearb_id, '')
            ), 'B') ||
            setweight(to_tsvector('german',
                coalesce(m2.anm_melder, '') || ' ' || coalesce(m2.anm_bearbeiter, '')
            ), 'D') AS sv
        FROM meldungen m2
        LEFT JOIN melduser mu ON m2.id = mu.id_meldung
        LEFT JOIN users u ON mu.id_user = u.id
        WHERE m2.fo_zuordnung IS NULL
          AND m2.id = target_id
    ) sub
    WHERE m.id = sub.id;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade():
    op.execute(SEARCH_VECTOR_FUNCTION)
    op.execute(TRIGGER_MELDUNGEN)
    op.execute(RECOMPUTE_FUNCTION)
    op.execute(TRIGGER_FUNDORTE)
    op.execute(TRIGGER_BESCHREIBUNG)
    op.execute(TRIGGER_USERS)
    op.execute(REPAIR_BACKFILL)


def downgrade():
    op.execute(OLD_TRIGGER_MELDUNGEN)
    op.execute(OLD_RECOMPUTE_FUNCTION)
    op.execute(OLD_TRIGGER_FUNDORTE)
    op.execute(OLD_TRIGGER_BESCHREIBUNG)
    op.execute(OLD_TRIGGER_USERS)
    op.execute(
        "DROP FUNCTION IF EXISTS meldung_search_vector(integer, integer, text, text, text)"
    )
