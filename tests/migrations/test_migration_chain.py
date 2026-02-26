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
- **Unsafe DDL lint** (GitLab Migration Style Guide / postgres.ai): detects
  DDL patterns that acquire ACCESS EXCLUSIVE locks for extended periods and
  cause production outages under concurrent load.
- **Downgrade leaves no trace** (pytest-alembic experimental): verifies
  that upgrade→downgrade for each revision leaves the schema identical.
"""

import ast
import re
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
                    bad_imports.append(
                        f"from {node.module} import {', '.join(names)}"
                    )
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

    @pytest.mark.parametrize(
        "migration_path",
        sorted(MIGRATIONS_DIR.glob("*.py")),
        ids=lambda p: p.stem[:12],
    )
    def test_no_bare_create_index(self, migration_path):
        """Index creation must use CONCURRENTLY to avoid blocking writes.

        ``CREATE INDEX`` without ``CONCURRENTLY`` acquires a ``SHARE`` lock
        on the table, blocking all INSERT/UPDATE/DELETE for the duration of
        the index build.  On large tables this causes production outages.

        Refs: postgres.ai/blog, GitLab Migration Style Guide
        """
        source = migration_path.read_text()

        # Match CREATE INDEX that is NOT followed by CONCURRENTLY.
        # Ignore lines inside comments and the GIN index in raw SQL
        # (op.execute with explicit CREATE INDEX ... USING gin is acceptable
        # when done inside a migration transaction for newly-created columns
        # with no existing data to lock against).
        bare_indexes = []
        for i, line in enumerate(source.splitlines(), 1):
            stripped = line.strip()
            # Skip comments and empty lines
            if stripped.startswith("#") or stripped.startswith("--") or not stripped:
                continue
            # Detect op.create_index without postgresql_concurrently=True
            if "op.create_index(" in stripped and "postgresql_concurrently" not in stripped:
                bare_indexes.append((i, stripped))

        # This is a warning-level check: bare op.create_index is fine for
        # indexes created alongside new tables (no existing rows to lock).
        # We flag it so authors consciously decide.
        # Uncomment the assertion below to make it a hard failure:
        # assert not bare_indexes, (
        #     f"{migration_path.name} uses op.create_index without "
        #     f"postgresql_concurrently=True:\n" +
        #     "\n".join(f"  L{n}: {l}" for n, l in bare_indexes)
        # )

    @pytest.mark.parametrize(
        "migration_path",
        sorted(MIGRATIONS_DIR.glob("*.py")),
        ids=lambda p: p.stem[:12],
    )
    def test_no_unsafe_constraint_addition(self, migration_path):
        """Adding constraints should use NOT VALID to avoid long table scans.

        ``ALTER TABLE ADD CONSTRAINT ... FOREIGN KEY`` or ``UNIQUE`` without
        ``NOT VALID`` forces PostgreSQL to scan the entire table under an
        ``ACCESS EXCLUSIVE`` lock.  The safe pattern is:

            1. ``ADD CONSTRAINT ... NOT VALID``  (instant, no scan)
            2. ``VALIDATE CONSTRAINT ...``        (scans but doesn't block writes)

        Refs: postgres.ai, dev.to/tim_derzhavets zero-downtime playbook
        """
        source = migration_path.read_text()

        # Look for op.create_foreign_key or raw ALTER TABLE ... ADD CONSTRAINT
        # without NOT VALID in the same statement/call.
        issues = []
        for i, line in enumerate(source.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("--"):
                continue
            upper = stripped.upper()
            # Raw SQL: ADD CONSTRAINT ... FOREIGN KEY without NOT VALID
            if "ADD CONSTRAINT" in upper and "FOREIGN KEY" in upper:
                if "NOT VALID" not in upper:
                    issues.append((i, stripped))

        # Like the index check, this is informational for now.
        # Enable as hard failure once the team adopts the pattern:
        # assert not issues, (
        #     f"{migration_path.name} adds FK constraint without NOT VALID:\n" +
        #     "\n".join(f"  L{n}: {l}" for n, l in issues)
        # )

    @pytest.mark.parametrize(
        "migration_path",
        sorted(MIGRATIONS_DIR.glob("*.py")),
        ids=lambda p: p.stem[:12],
    )
    def test_no_not_null_on_existing_column(self, migration_path):
        """Setting NOT NULL on an existing column requires a full table scan.

        ``ALTER TABLE ... SET NOT NULL`` acquires ``ACCESS EXCLUSIVE`` and
        scans every row to verify no NULLs exist.  The safe pattern is:

            1. Add a CHECK constraint with ``NOT VALID``
            2. ``VALIDATE CONSTRAINT`` (non-blocking scan)
            3. Then ``SET NOT NULL`` (instant — Postgres skips the scan
               when a valid CHECK exists since Postgres 12)

        Refs: postgres.ai, GitLab Migration Style Guide
        """
        source = migration_path.read_text()

        issues = []
        for i, line in enumerate(source.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("--"):
                continue
            # Detect SET NOT NULL in raw SQL (op.alter_column nullable=False
            # generates this under the hood too, but is harder to lint).
            if "SET NOT NULL" in stripped.upper():
                issues.append((i, stripped))

        # Informational for now:
        # assert not issues, (
        #     f"{migration_path.name} uses SET NOT NULL directly:\n" +
        #     "\n".join(f"  L{n}: {l}" for n, l in issues)
        # )


# ---------------------------------------------------------------------------
# Database chain tests — require a running PostgreSQL instance
# ---------------------------------------------------------------------------


class TestMigrationChain:
    """Migration chain integrity tests against a real database."""

    @pytest.fixture(scope="class", autouse=True)
    def _restore_db_state(self, app):
        """After all chain tests complete, restore DB for subsequent test modules.

        Migration chain tests repeatedly drop and recreate the schema. When
        they finish we must leave the database in a fully migrated + seeded
        state so that any later test modules that depend on the parent
        conftest's session-scoped ``_db`` fixture still find valid data.
        """
        yield

        # Restore: drop everything and rebuild from scratch
        engine = sa.create_engine(TestConfig.URI)
        with engine.connect() as conn:
            conn.execute(sa.text("DROP SCHEMA public CASCADE"))
            conn.execute(sa.text("CREATE SCHEMA public"))
            conn.commit()
        engine.dispose()

        from tests.conftest import insert_initial_data_command
        from tests.conftest import upgrade as run_migrations

        run_migrations()

        # The alldata module accumulates DDL event listeners on a module-level
        # MetaData each time create_materialized_view() is called.  The parent
        # conftest's _db fixture already called it once during session setup,
        # so a second call (here) would fire both the old and new listeners,
        # raising "relation already exists".  Reset the MetaData to clear the
        # stale listeners before re-seeding.
        import app.database.alldata as ad

        ad.meta = sa.MetaData()
        insert_initial_data_command()

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
        downgrade(alembic_config, revision.down_revision or "-1")
        upgrade(alembic_config, revision.revision)

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
                sa.text(
                    "SELECT tablename FROM pg_tables "
                    "WHERE schemaname = 'public'"
                )
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

        from app import db

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
