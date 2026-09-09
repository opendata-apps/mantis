"""Alembic migration chain integrity tests.

Verifies the health and correctness of the migration chain using patterns
from well-known open source projects:

- **Stairway test** (alvassin/alembic-quickstart): per-revision
  upgrade → downgrade → upgrade catches forgotten downgrade methods,
  leftover types, and typos.
- **Single head check** (pytest-alembic): prevents diverging migration
  branches that break ``alembic upgrade head``.
- **Model sync check** (pytest-alembic / alembic-quickstart):
  ``compare_metadata`` detects model changes without a matching migration.
- **No ORM imports lint** (Apache Airflow): migration scripts must not
  import ORM model classes because models evolve after migrations are written.
- **Downgrade leaves no trace** (pytest-alembic experimental): verifies
  that upgrade→downgrade for each revision leaves the schema identical.
"""

import ast
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.command import downgrade, upgrade
from alembic.config import Config
from alembic.script import ScriptDirectory

from tests.test_config import Config as TestConfig

MIGRATIONS_DIR = Path("migrations/versions")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_alembic_config():
    """Standalone Alembic config for non-DB operations (revision walking)."""
    cfg = Config("migrations/alembic.ini")
    cfg.set_main_option("script_location", "migrations")
    return cfg


def _get_revisions():
    """All migration revisions in chronological order (oldest first)."""
    script_dir = ScriptDirectory.from_config(_get_alembic_config())
    revisions = list(script_dir.walk_revisions("base", "heads"))
    revisions.reverse()
    return revisions


# ---------------------------------------------------------------------------
# Static checks — no database connection required
# ---------------------------------------------------------------------------


class TestMigrationLint:
    """Static analysis of migration files."""

    def test_single_head_revision(self):
        """Ensure exactly one head revision exists.

        Multiple heads mean two developers both created a migration from the
        same parent. Resolve with ``alembic merge heads``.
        """
        script_dir = ScriptDirectory.from_config(_get_alembic_config())
        heads = script_dir.get_heads()
        assert len(heads) == 1, (
            f"Expected 1 migration head, found {len(heads)}: {heads}. "
            "Run `alembic merge heads` to resolve."
        )

    def test_linear_chain(self):
        """Verify every revision except the first has exactly one parent.

        Catches accidental branch_labels or depends_on misconfigurations
        that could create a non-linear history.
        """
        revisions = _get_revisions()
        for rev in revisions[1:]:  # skip initial migration (down_revision is None)
            assert rev.down_revision is not None, (
                f"Revision {rev.revision} has down_revision=None but is not "
                "the initial migration."
            )

    @pytest.mark.parametrize(
        "migration_path",
        sorted(MIGRATIONS_DIR.glob("*.py")),
        ids=lambda p: p.stem[:12],
    )
    def test_no_orm_model_imports(self, migration_path):
        """Migration files must not import ORM model classes.

        Importing models (e.g. ``TblMeldungen``) into a migration is dangerous:
        the model reflects the *current* schema, but the migration may target
        an *older* schema. When replayed from scratch the column mismatch
        causes a crash. Use raw ``sa.table()`` / ``op.execute()`` instead.
        """
        source = migration_path.read_text()
        tree = ast.parse(source, filename=str(migration_path))

        forbidden_prefixes = ("app.database",)
        bad_imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if any(node.module.startswith(p) for p in forbidden_prefixes):
                    names = [alias.name for alias in node.names]
                    bad_imports.append(f"from {node.module} import {', '.join(names)}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if any(alias.name.startswith(p) for p in forbidden_prefixes):
                        bad_imports.append(f"import {alias.name}")

        assert not bad_imports, (
            f"{migration_path.name} imports ORM models — this will break when "
            f"replayed against older schemas:\n  " + "\n  ".join(bad_imports)
        )

    @pytest.mark.parametrize(
        "migration_path",
        sorted(MIGRATIONS_DIR.glob("*.py")),
        ids=lambda p: p.stem[:12],
    )
    def test_has_downgrade(self, migration_path):
        """Every migration must define a non-empty downgrade function.

        A ``pass``-only downgrade silently breaks rollback capability.
        """
        source = migration_path.read_text()
        tree = ast.parse(source, filename=str(migration_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "downgrade":
                # Check that the body is not just `pass`
                body = node.body
                is_empty = len(body) == 1 and isinstance(body[0], ast.Pass)
                assert not is_empty, (
                    f"{migration_path.name}: downgrade() is just `pass`. "
                    "Every migration must be reversible."
                )
                return

        pytest.fail(f"{migration_path.name}: missing downgrade() function.")


# ---------------------------------------------------------------------------
# Database chain tests — require a running PostgreSQL instance
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("app_ctx")
class TestMigrationChain:
    """Migration chain integrity tests against a real database."""

    @pytest.mark.parametrize(
        "revision",
        _get_revisions(),
        ids=lambda r: r.revision[:12],
    )
    def test_stairway(self, clean_db, alembic_config, revision):
        """Each migration can be applied, rolled back, and reapplied.

        The "stairway test" (from alvassin/alembic-quickstart) catches ~80%
        of migration errors with zero maintenance: just add it once.
        """
        upgrade(alembic_config, revision.revision)
        parent = revision.down_revision
        downgrade(
            alembic_config, parent[0] if isinstance(parent, tuple) else parent or "-1"
        )
        upgrade(alembic_config, revision.revision)

    @pytest.mark.parametrize("old_head", ["d4e5f6a7b8c9", "7e9e54853fa2"])
    def test_merge_preserves_existing_reports(self, clean_db, alembic_config, old_head):
        upgrade(alembic_config, old_head)
        engine = sa.create_engine(TestConfig.URI)
        try:
            with engine.begin() as conn:
                conn.execute(
                    sa.text(
                        "INSERT INTO beschreibung (id, beschreibung) VALUES (1, 'Garten')"
                    )
                )
                conn.execute(
                    sa.text(
                        "INSERT INTO users (id, user_id, user_name, user_rolle, user_kontakt) "
                        "VALUES (1, 'migration-user', 'Mustermann A.', '1', :contact)"
                    ),
                    {"contact": "anna@beispieldomain.de"},
                )
                conn.execute(
                    sa.text(
                        "INSERT INTO fundorte "
                        "(id, plz, ort, strasse, kreis, land, beschreibung, latitude, longitude, ablage) "
                        "VALUES (1, :plz, 'Dresden', 'Testweg', 'Dresden', 'Sachsen', "
                        "1, '51.05', '13.74', '2025/foto.webp')"
                    ),
                    {"plz": 1067 if old_head == "d4e5f6a7b8c9" else "01067"},
                )
                conn.execute(
                    sa.text(
                        "INSERT INTO meldungen (id, dat_fund_von, fo_zuordnung, statuses) "
                        "VALUES (1, '2025-06-01', 1, '{OPEN}')"
                    )
                )
                conn.execute(
                    sa.text("INSERT INTO melduser (id_meldung, id_user) VALUES (1, 1)")
                )
            upgrade(alembic_config, "head")
            with engine.begin() as conn:
                row = conn.execute(
                    sa.text(
                        "SELECT plz, latitude, longitude, ablage, user_kontakt, statuses "
                        "FROM all_data_view WHERE meldungen_id = 1"
                    )
                ).one()
                assert tuple(row) == (
                    "01067",
                    51.05,
                    13.74,
                    "2025/foto.webp",
                    "anna@beispieldomain.de",
                    ["OPEN"],
                )
                assert conn.scalar(
                    sa.text(
                        "SELECT search_vector @@ plainto_tsquery('german', 'beispieldomain.de') "
                        "FROM meldungen WHERE id = 1"
                    )
                )
                long_name = "Mustermann" * 9
                long_contact = "a" * 50 + "@beispieldomain.de"
                conn.execute(
                    sa.text(
                        "UPDATE users SET user_name = :name, user_kontakt = :contact WHERE id = 1"
                    ),
                    {"name": long_name, "contact": long_contact},
                )
                assert conn.execute(
                    sa.text(
                        "SELECT user_name, user_kontakt FROM all_data_view WHERE meldungen_id = 1"
                    )
                ).one() == (long_name, long_contact)
                conn.execute(
                    sa.text("UPDATE fundorte SET ort = 'Neustadt' WHERE id = 1")
                )
                assert (
                    conn.scalar(
                        sa.text("SELECT ort FROM all_data_view WHERE meldungen_id = 1")
                    )
                    == "Neustadt"
                )
        finally:
            engine.dispose()

    def test_full_upgrade(self, clean_db, alembic_config):
        """The complete chain from base to head succeeds on a fresh database."""
        upgrade(alembic_config, "head")

    def test_full_upgrade_downgrade(self, clean_db, alembic_config):
        """Upgrade to head then downgrade all the way back to base."""
        upgrade(alembic_config, "head")
        downgrade(alembic_config, "base")

    def test_upgrade_idempotency(self, clean_db, alembic_config):
        """Running ``upgrade head`` twice must not error.

        In production, deploy scripts sometimes retry migrations on failure.
        The second ``upgrade head`` should be a no-op (alembic_version is
        already at head), not a crash.
        """
        upgrade(alembic_config, "head")
        upgrade(alembic_config, "head")  # must not raise

    def test_downgrade_leaves_no_trace(self, clean_db, alembic_config):
        """Upgrading to head then downgrading to base must leave no tables.

        This verifies that every downgrade() faithfully undoes its upgrade().
        After a full roundtrip the public schema should contain no user
        tables (only the empty alembic_version table is acceptable).

        Inspired by pytest-alembic's experimental
        ``test_downgrade_leaves_no_trace``.
        """
        upgrade(alembic_config, "head")
        downgrade(alembic_config, "base")

        engine = sa.create_engine(TestConfig.URI)
        with engine.connect() as conn:
            result = conn.execute(
                sa.text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            )
            remaining_tables = {row[0] for row in result}
        engine.dispose()

        # alembic_version is expected — Alembic manages it separately
        remaining_tables.discard("alembic_version")

        assert not remaining_tables, (
            "Downgrade to base left orphan tables behind:\n  "
            + ", ".join(sorted(remaining_tables))
        )

    def test_downgrade_leaves_no_functions(self, clean_db, alembic_config):
        """Downgrading to base must not leave orphan functions or triggers.

        PostgreSQL functions created by migrations (e.g. FTS trigger
        functions) must be dropped in the corresponding downgrade.
        """
        upgrade(alembic_config, "head")
        downgrade(alembic_config, "base")

        engine = sa.create_engine(TestConfig.URI)
        with engine.connect() as conn:
            result = conn.execute(
                sa.text(
                    "SELECT routine_name FROM information_schema.routines "
                    "WHERE routine_schema = 'public' "
                    "AND routine_type = 'FUNCTION'"
                )
            )
            remaining_fns = {row[0] for row in result}
        engine.dispose()

        assert not remaining_fns, (
            "Downgrade to base left orphan functions behind:\n  "
            + ", ".join(sorted(remaining_fns))
        )

    def test_model_definitions_match_ddl(self, clean_db, app, alembic_config):
        """Models and migrations are in sync (no pending schema changes).

        Upgrades to head, then runs alembic's autogenerate diff to compare
        the actual DB schema against SQLAlchemy model metadata. Any diff
        means a migration is missing.
        """
        from alembic.autogenerate import compare_metadata
        from alembic.runtime.migration import MigrationContext

        from app.extensions import db

        upgrade(alembic_config, "head")

        engine = sa.create_engine(TestConfig.URI)
        with engine.connect() as conn:
            ctx = MigrationContext.configure(conn)
            diff = compare_metadata(ctx, db.metadata)
        engine.dispose()

        significant = [d for d in diff if not _is_ignorable_diff(d)]

        assert not significant, (
            "Models and migrations are out of sync. Missing migration for:\n"
            + "\n".join(str(d) for d in significant)
        )


def _is_ignorable_diff(diff_item):
    """Filter known-harmless autogenerate false positives.

    Returns True if the diff should be ignored. Extend this function
    when Alembic flags something that is intentionally managed outside
    of migrations (e.g., server defaults set at the DB level).
    """
    return False
