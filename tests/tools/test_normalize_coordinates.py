from datetime import datetime

from app.database.models import TblFundortBeschreibung, TblFundorte, TblMeldungen


class TestNormalizeCoordinatesCommand:
    def test_normalize_coordinates_updates_legacy_decimal_format(self, app, session):
        location_type = session.get(TblFundortBeschreibung, 1)
        assert location_type is not None

        location = TblFundorte(
            mtb="3644",
            longitude="13,404954",
            latitude=" 52,520008 ",
            ort="Berlin",
            land="Berlin",
            kreis="Mitte",
            strasse="Alexanderplatz 1",
            plz=10178,
            amt="11000000",
            ablage="legacy.webp",
            beschreibung=location_type.id,
        )
        session.add(location)
        session.flush()

        session.add(
            TblMeldungen(
                dat_fund_von=datetime.now().date(),
                dat_meld=datetime.now().date(),
                fo_zuordnung=location.id,
                statuses=["APPR"],
                deleted=False,
                art_m=1,
            )
        )
        session.commit()

        result = app.test_cli_runner().invoke(args=["normalize-coordinates"])

        assert result.exit_code == 0
        session.expire_all()
        normalized = session.get(TblFundorte, location.id)
        assert normalized is not None
        assert normalized.latitude == "52.520008"
        assert normalized.longitude == "13.404954"
        assert "Scanning " in result.output
        assert "Normalized " in result.output

    def test_normalize_coordinates_reports_invalid_rows(self, app, session):
        location_type = session.get(TblFundortBeschreibung, 1)
        assert location_type is not None

        location = TblFundorte(
            mtb="",
            longitude="13,404954",
            latitude="north",
            ort="Broken",
            land="Berlin",
            kreis="Mitte",
            strasse="Alexanderplatz 1",
            plz=10178,
            amt="11000000",
            ablage="broken.webp",
            beschreibung=location_type.id,
        )
        session.add(location)
        session.commit()

        result = app.test_cli_runner().invoke(args=["normalize-coordinates"])

        assert result.exit_code == 1
        assert "Found 1 Fundorte with invalid coordinates." in result.output
        session.expire_all()
        unchanged = session.get(TblFundorte, location.id)
        assert unchanged is not None
        assert unchanged.latitude == "north"
        assert unchanged.longitude == "13,404954"
