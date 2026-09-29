"""Search literal word prefixes with consistent German transliterations."""

from alembic import op

revision = "c2a7f419d830"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None

NORMALIZE = """
CREATE FUNCTION reviewer_search_normalize(value text) RETURNS text AS $$
    SELECT replace(replace(replace(replace(lower(normalize(value)),
        'ä', 'ae'), 'ö', 'oe'), 'ü', 'ue'), 'ß', 'ss');
$$ LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE;
"""

SEARCH_VECTOR = """
CREATE OR REPLACE FUNCTION meldung_search_vector(
    p_meldung_id integer,
    p_fo_zuordnung integer,
    p_bearb_id text,
    p_anm_melder text,
    p_anm_bearbeiter text
) RETURNS tsvector AS $$
    SELECT setweight(to_tsvector('simple', reviewer_search_normalize(
               concat_ws(' ', f.ort, f.kreis, f.land, f.plz))), 'A')
        || setweight(to_tsvector('simple', reviewer_search_normalize(
               concat_ws(' ', u.user_name, u.user_kontakt,
                         replace(u.user_kontakt, '@', ' '), u.user_id, p_bearb_id))), 'B')
        || setweight(to_tsvector('simple', reviewer_search_normalize(
               concat_ws(' ', f.strasse, f.amt, f.mtb, b.beschreibung))), 'C')
        || setweight(to_tsvector('simple', reviewer_search_normalize(
               concat_ws(' ', p_anm_melder, p_anm_bearbeiter))), 'D')
    FROM (SELECT 1) AS anchor
    LEFT JOIN fundorte f ON f.id = p_fo_zuordnung
    LEFT JOIN beschreibung b ON b.id = f.beschreibung
    LEFT JOIN melduser mu ON mu.id_meldung = p_meldung_id
    LEFT JOIN users u ON u.id = mu.id_user
    LIMIT 1;
$$ LANGUAGE sql STABLE;
"""

OLD_SEARCH_VECTOR = """
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

BACKFILL = """
UPDATE meldungen m
SET search_vector = meldung_search_vector(
    m.id, m.fo_zuordnung, m.bearb_id, m.anm_melder, m.anm_bearbeiter);
"""


def upgrade():
    op.execute(NORMALIZE)
    op.execute(SEARCH_VECTOR)
    op.execute(BACKFILL)


def downgrade():
    op.execute(OLD_SEARCH_VECTOR)
    op.execute(BACKFILL)
    op.execute("DROP FUNCTION reviewer_search_normalize(text)")
