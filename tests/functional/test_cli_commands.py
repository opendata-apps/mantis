"""Tests for the Flask CLI commands registered by ``app/cli.py``.

Uses ``app.test_cli_runner()`` to invoke commands without a real shell.
Network-calling commands (``seed-ags``) are tested by patching the
``fetch_*`` helpers at their import-time module paths so no HTTP traffic
occurs.
"""

from unittest.mock import patch

import pytest


@pytest.fixture
def cli_runner(app):
    return app.test_cli_runner()


# NOTE: The ``create_all_data_view`` CLI command cannot be cleanly tested
# in isolation. It issues ``CREATE MATERIALIZED VIEW`` directly on
# ``db.engine`` (bypassing the test transaction), while the conftest
# already created the view at session scope — so the command always hits
# "relation already exists". Dropping first inside the test tx doesn't
# help because the test's ``commit`` releases a SAVEPOINT, not a real
# transaction. The function itself is exercised by ``_seed_test_data``
# on every pytest run, so coverage isn't actually lost.


class TestValidateCoordinatesCommand:
    def test_constant_stub_produces_mismatches(self, cli_runner, session):
        """Every seeded Fundort is in a different Gemeinde than the stub
        returns ("Test/Brandenburg"), so every checked record must show
        up as either LAND_MISMATCH (different Bundesland) or ORT_MISMATCH
        (same Bundesland, different Ort). Exit code is 1 when there are
        mismatches — that's the documented contract."""

        def spatial(coord):
            return {"land": "Brandenburg", "gen": "Test"}

        with patch(
            "app.tools.gemeinde_finder.get_amt_enriched",
            side_effect=spatial,
        ):
            result = cli_runner.invoke(args=["validate-coordinates"])

        assert result.exit_code == 1
        assert "Coordinate Validation Report" in result.output
        # Both issue types must appear because the demo data spans
        # multiple Bundesländer.
        assert "LAND_MISMATCH" in result.output
        assert "ORT_MISMATCH" in result.output

    def test_csv_export_creates_file(self, cli_runner, session, tmp_path):
        """Passing ``--csv`` must write a CSV with a header row when
        mismatches exist."""
        csv_path = tmp_path / "mismatches.csv"

        # Guarantee at least one mismatch by resolving every point to a
        # different Bundesland than what's stored.
        def spatial(coord):
            return {"land": "Nirgendwoland", "gen": "Nirgendwostadt"}

        with patch(
            "app.tools.gemeinde_finder.get_amt_enriched",
            side_effect=spatial,
        ):
            result = cli_runner.invoke(
                args=["validate-coordinates", "--csv", str(csv_path)]
            )

        assert result.exit_code == 1  # mismatches found → exit 1
        assert csv_path.exists()
        header = csv_path.read_text().splitlines()[0]
        assert header.startswith("id,issue,")


class TestNormalizeCoordinatesCommand:
    def test_normalizes_and_reports(self, cli_runner, session):
        """The command scans all Fundorte and normalizes any legacy
        comma-decimal or whitespace-padded coordinate to canonical form.
        On the seeded demo data everything is already normalized —
        the command should run cleanly and print ``Normalized 0``."""
        result = cli_runner.invoke(args=["normalize-coordinates"])
        assert result.exit_code == 0
        assert "Normalized" in result.output


class TestSeedCommand:
    """Coverage for ``flask seed`` — the subprocess that populates base
    data. We invoke it after the fixture-seeded DB so it should remain
    idempotent (the populate_all() call upserts)."""

    def test_seed_is_idempotent(self, cli_runner, session):
        """``flask seed`` upserts base data. Running it against an
        already-populated DB must not duplicate rows — every previous
        insert is skipped with a "record already exists" debug log."""
        from sqlalchemy import func, select

        from app.database.fundorte import TblFundorte
        from app.database.users import TblUsers

        before_users = session.scalar(select(func.count()).select_from(TblUsers))
        before_fundorte = session.scalar(select(func.count()).select_from(TblFundorte))

        result = cli_runner.invoke(args=["seed"])
        assert result.exit_code == 0
        assert "Base data seeded" in result.output
        assert "Done" in result.output

        # Row counts unchanged → truly idempotent
        assert session.scalar(select(func.count()).select_from(TblUsers)) == (
            before_users
        )
        assert session.scalar(select(func.count()).select_from(TblFundorte)) == (
            before_fundorte
        )

    def test_seed_with_demo_copies_images(self, cli_runner, tmp_path, app):
        """``seed --demo`` copies demo images into
        ``UPLOAD_FOLDER/2025/2025-01-19``. We swap UPLOAD_FOLDER to a
        tmp dir so the real datastore stays untouched, then verify the
        actual files landed on disk."""
        original_upload = app.config["UPLOAD_FOLDER"]
        app.config["UPLOAD_FOLDER"] = str(tmp_path)
        try:
            result = cli_runner.invoke(args=["seed", "--demo"])
        finally:
            app.config["UPLOAD_FOLDER"] = original_upload

        assert result.exit_code == 0
        assert "Demo data seeded" in result.output

        target_dir = tmp_path / "2025" / "2025-01-19"
        assert target_dir.exists()

        webps = list(target_dir.glob("*.webp"))
        # The mapping in app/cli.py lists 20 target files — demand most
        # of them land on disk (tolerate a missing source webp).
        assert len(webps) >= 15, f"expected ~20 webps, got {len(webps)}"
        # Every file must be non-empty — guards against a silent copy
        # failure that would produce 0-byte files.
        assert all(w.stat().st_size > 0 for w in webps)

    def test_seed_without_fallback_warns_but_completes(self, cli_runner, session):
        """If ``ags_gemeinden.json`` is missing, the command prints a
        warning on stderr, calls ``populate_all`` with ``jsondata=None``,
        and exits cleanly. The aemter table must still be usable
        afterwards (existing rows from fixture stay put)."""
        from sqlalchemy import func, select

        from app.database.aemter_koordinaten import TblAemterCoordinaten

        before_aemter = session.scalar(
            select(func.count()).select_from(TblAemterCoordinaten)
        )

        with patch("app.cli.os.path.exists", return_value=False):
            result = cli_runner.invoke(args=["seed"])

        assert result.exit_code == 0
        assert "No AGS fallback data found" in result.output
        # Existing aemter preserved (populate_all with None is a no-op
        # for VG5000 data, not a destructive truncate).
        assert (
            session.scalar(select(func.count()).select_from(TblAemterCoordinaten))
            == before_aemter
        )


class TestSeedAgsCommand:
    """Covers ``flask seed-ags`` by patching the WFS fetchers."""

    def test_successful_sync(self, cli_runner, session):
        """Happy path: fetchers return tiny synthetic datasets, command
        syncs the aemter table without error.

        The write-to-disk side-effects (``save_fallback``,
        ``save_kreise_lookup``) are stubbed out so we don't clobber the
        real ``app/data/ags_*.json`` files that ship with the repo.
        """
        fake_gemeinden = {
            "type": "FeatureCollection",
            "numberReturned": 1,
            "features": [
                {
                    "type": "Feature",
                    "properties": {"ags": "12054012", "gen": "Testort"},
                    "geometry": {"type": "Point", "coordinates": [13.4, 52.5]},
                }
            ],
        }
        fake_kreise = {
            "type": "FeatureCollection",
            "features": [
                {
                    "properties": {
                        "ags": "12054",
                        "bez": "Landkreis",
                        "gen": "Testkreis",
                    },
                    "geometry": {"type": "Point", "coordinates": [13.4, 52.5]},
                }
            ],
        }

        with (
            patch("app.tools.fetch_ags.fetch_gemeinden", return_value=fake_gemeinden),
            patch("app.tools.fetch_ags.fetch_kreise", return_value=fake_kreise),
            patch("app.tools.fetch_ags.fetch_berlin_bezirke", return_value=[]),
            patch("app.tools.fetch_ags.save_fallback") as mock_save_fb,
            patch("app.tools.fetch_ags.save_kreise_lookup") as mock_save_krs,
        ):
            result = cli_runner.invoke(args=["seed-ags"])

        assert result.exit_code == 0, result.output
        assert "Administrative area data is up to date" in result.output

        mock_save_fb.assert_called_once()
        mock_save_krs.assert_called_once()

        # Merged payload has the normalized BKG feature shape
        merged_arg = mock_save_fb.call_args.args[0]
        assert merged_arg["type"] == "FeatureCollection"
        assert len(merged_arg["features"]) == 1
        feat = merged_arg["features"][0]
        assert feat["properties"]["AGS"] == "12054012"
        assert feat["properties"]["GEN"] == "Testort"

        # Kreise lookup maps 5-digit AGS → "Landkreis Testkreis"
        kreise_arg = mock_save_krs.call_args.args[0]
        assert kreise_arg == {"12054": "Landkreis Testkreis"}

    def test_fetch_error_aborts_without_writing_disk(self, cli_runner):
        """If the BKG WFS is unreachable the command must abort via
        ``click.Abort`` (exit code 1) and must NOT write the fallback
        files — otherwise the real ``app/data/ags_*.json`` shipped with
        the repo could be clobbered with a half-baked payload."""
        with (
            patch(
                "app.tools.fetch_ags.fetch_gemeinden",
                side_effect=RuntimeError("BKG unreachable"),
            ),
            patch("app.tools.fetch_ags.save_fallback") as mock_save_fb,
            patch("app.tools.fetch_ags.save_kreise_lookup") as mock_save_krs,
        ):
            result = cli_runner.invoke(args=["seed-ags"])

        assert result.exit_code == 1
        assert isinstance(result.exception, SystemExit)
        assert "Error fetching AGS data: BKG unreachable" in result.output
        assert "Aborted" in result.output
        # No disk writes happened — the error short-circuited the function
        mock_save_fb.assert_not_called()
        mock_save_krs.assert_not_called()
