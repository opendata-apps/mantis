"""Tests for the Flask CLI commands registered by ``app/cli.py``.

Uses ``app.test_cli_runner()`` to invoke commands without a real shell.
Network-calling commands (``seed-ags``) are tested by patching the
``fetch_*`` helpers at their import-time module paths so no HTTP traffic
occurs.
"""

from unittest.mock import patch
from pathlib import Path
import json

import pytest


@pytest.fixture
def cli_runner(app, _db):
    return app.test_cli_runner()


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

        # Seeding base data does not add reporters or sightings.
        assert session.scalar(select(func.count()).select_from(TblUsers)) == (
            before_users
        )
        assert session.scalar(select(func.count()).select_from(TblFundorte)) == (
            before_fundorte
        )

        from app.database.models import TblAemterCoordinaten, TblFundortBeschreibung

        descriptions = select(
            TblFundortBeschreibung.id, TblFundortBeschreibung.beschreibung
        ).order_by(TblFundortBeschreibung.id)
        areas = select(
            TblAemterCoordinaten.ags,
            TblAemterCoordinaten.gen,
            TblAemterCoordinaten.properties,
        ).order_by(TblAemterCoordinaten.ags)
        before_descriptions = session.execute(descriptions).all()
        before_areas = session.execute(areas).all()
        assert before_descriptions and before_areas
        assert cli_runner.invoke(args=["seed"]).exit_code == 0
        assert session.execute(descriptions).all() == before_descriptions
        assert session.execute(areas).all() == before_areas

    def test_seed_with_demo_copies_images(self, cli_runner, app, session):
        """``seed --demo`` stores every referenced demo image in the upload root."""
        upload_root = Path(app.config["UPLOAD_FOLDER"])
        result = cli_runner.invoke(args=["seed", "--demo"])

        assert result.exit_code == 0
        assert "Demo data seeded" in result.output

        target_dir = upload_root / "2025" / "2025-01-19"
        assert target_dir.exists()

        from sqlalchemy import select
        from app.database.models import TblFundorte, TblMeldungen

        image_paths = session.scalars(
            select(TblFundorte.ablage)
            .join(TblMeldungen)
            .where(TblMeldungen.id.between(1, 20))
        ).all()
        assert len(image_paths) == 20
        assert all(
            (upload_root / path).is_file() and (upload_root / path).stat().st_size > 0
            for path in image_paths
        )

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


class TestRecalculateMtbCommand:
    """``flask recalculate-mtb`` re-derives stored sheet numbers."""

    def _fundort(self, session):
        from app.database.fundorte import TblFundorte
        from sqlalchemy import select

        return session.scalars(select(TblFundorte).order_by(TblFundorte.id)).first()

    def test_dry_run_reports_without_writing(self, cli_runner, session):
        fundort = self._fundort(session)
        fundort.mtb = "0000"
        session.commit()

        def spatial(coord):
            return {
                "ags": "12062289",
                "gen": "Lebusa",
                "land": "Brandenburg",
                "kreis": "Elbe-Elster",
                "amt_string": "12062289 -- Lebusa",
            }

        with patch(
            "app.tools.location_enrichment.get_amt_enriched", side_effect=spatial
        ):
            result = cli_runner.invoke(args=["recalculate-mtb"])

        assert result.exit_code == 0, result.output
        assert "Dry run" in result.output
        session.refresh(fundort)
        assert fundort.mtb == "0000", "a dry run must not touch the database"

    def test_commit_writes_the_corrected_sheet(self, cli_runner, session):
        fundort = self._fundort(session)
        # Lebusa, Landkreis Elbe-Elster. Pinned so the expected sheet can be
        # the number off the printed map rather than whatever get_mtb returns.
        fundort.latitude = "51.789314"
        fundort.longitude = "13.405689"
        fundort.mtb = "0000"
        session.commit()

        def spatial(coord):
            return {
                "ags": "12062289",
                "gen": "Lebusa",
                "land": "Brandenburg",
                "kreis": "Elbe-Elster",
                "amt_string": "12062289 -- Lebusa",
            }

        with patch(
            "app.tools.location_enrichment.get_amt_enriched", side_effect=spatial
        ):
            result = cli_runner.invoke(args=["recalculate-mtb", "--commit"])

        assert result.exit_code == 0, result.output
        assert "Committed." in result.output
        session.refresh(fundort)
        assert fundort.mtb == "4246"
        assert fundort.amt == "12062289 -- Lebusa"


class TestSeedAgsCommand:
    """Covers ``flask seed-ags`` by patching the WFS fetchers."""

    def test_successful_sync(self, cli_runner, session, tmp_path, monkeypatch):
        import app.cli
        from sqlalchemy import select
        from app.database.models import TblAemterCoordinaten

        monkeypatch.setattr(app.cli, "__file__", str(tmp_path / "cli.py"))
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
        ):
            result = cli_runner.invoke(args=["seed-ags"])

        assert result.exit_code == 0, result.output
        assert "Administrative area data is up to date" in result.output

        merged_arg = json.loads((tmp_path / "data" / "ags_gemeinden.json").read_text())
        assert merged_arg["type"] == "FeatureCollection"
        assert len(merged_arg["features"]) == 1
        feat = merged_arg["features"][0]
        assert feat["properties"]["AGS"] == "12054012"
        assert feat["properties"]["GEN"] == "Testort"

        # Kreise lookup maps 5-digit AGS → "Landkreis Testkreis"
        kreise_arg = json.loads((tmp_path / "data" / "ags_kreise.json").read_text())
        assert kreise_arg == {"12054": "Landkreis Testkreis"}

        rows = session.scalars(select(TblAemterCoordinaten)).all()
        assert [(row.ags, row.gen, row.properties) for row in rows] == [
            (12054012, "Testort", {"type": "Point", "coordinates": [13.4, 52.5]})
        ]

    def test_fetch_error_preserves_saved_data(
        self, cli_runner, session, tmp_path, monkeypatch
    ):
        import app.cli
        from sqlalchemy import select
        from app.database.models import TblAemterCoordinaten

        monkeypatch.setattr(app.cli, "__file__", str(tmp_path / "cli.py"))
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        paths = [data_dir / "ags_gemeinden.json", data_dir / "ags_kreise.json"]
        for path in paths:
            path.write_text('{"existing": true}')
        before = [
            (row.ags, row.gen, row.properties)
            for row in session.scalars(
                select(TblAemterCoordinaten).order_by(TblAemterCoordinaten.ags)
            )
        ]
        with patch(
            "app.tools.fetch_ags.fetch_gemeinden",
            side_effect=RuntimeError("BKG unreachable"),
        ):
            result = cli_runner.invoke(args=["seed-ags"])
        assert result.exit_code == 1
        assert "BKG unreachable" in result.output
        assert [path.read_text() for path in paths] == ['{"existing": true}'] * 2
        after = [
            (row.ags, row.gen, row.properties)
            for row in session.scalars(
                select(TblAemterCoordinaten).order_by(TblAemterCoordinaten.ags)
            )
        ]
        assert after == before
