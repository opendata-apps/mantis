from app.tools.geo_grade_service import grade_fundort_fields


def test_grade_fundort_fields_returns_columns(app, session, monkeypatch):
    from app.tools import geo_grade_service as svc
    from app.tools.geo_names import NearestPlace

    monkeypatch.setattr(
        svc,
        "get_amt_enriched",
        lambda pt: {
            "land": "Brandenburg",
            "gen": "Schönborn",
            "kreis": "Elbe-Elster",
            "ags": 12062264,
        },
    )

    class _Idx:
        def nearest_places(self, pt):
            return [NearestPlace("Schadewitz", 12062264, "Elbe-Elster", 120.0)]

    monkeypatch.setattr(svc, "get_geo_names_index", lambda: _Idx())

    cols = grade_fundort_fields(
        51.58, 13.52, "Brandenburg", "Elbe-Elster", "Schadewitz"
    )
    assert cols["geo_grade"] == "HIGH"
    assert cols["geo_matched_level"] == "ORTSTEIL"
    assert "geo_graded_at" in cols
