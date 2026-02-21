"""Functional tests for gemeinde finder."""

import pytest
from sqlalchemy import delete
from app.tools.gemeinde_finder import get_amt_optimized, reload_gemeinde_cache
from app.database.aemter_koordinaten import TblAemterCoordinaten


class TestGemeindeOptimization:
    """Test the optimized gemeinde finder with real database."""

    @pytest.fixture(autouse=True)
    def setup(self, session):
        """Setup test data."""
        self.session = session

        # Clear any existing test data
        session.execute(
            delete(TblAemterCoordinaten).where(
                TblAemterCoordinaten.ags.in_([99999901, 99999902, 99999903])
            )
        )

        # Add test administrative areas
        test_areas = [
            TblAemterCoordinaten(
                ags=99999901,
                gen="Test Berlin Mitte",
                properties={
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [13.38, 52.50],
                            [13.42, 52.50],
                            [13.42, 52.54],
                            [13.38, 52.54],
                            [13.38, 52.50],
                        ]
                    ],
                },
            ),
            TblAemterCoordinaten(
                ags=99999902,
                gen="Test Potsdam",
                properties={
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [13.00, 52.35],
                            [13.15, 52.35],
                            [13.15, 52.45],
                            [13.00, 52.45],
                            [13.00, 52.35],
                        ]
                    ],
                },
            ),
            TblAemterCoordinaten(
                ags=1234567,  # Test with AGS < 10000000
                gen="Test Kleinstadt",
                properties={
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [12.00, 51.00],
                            [12.10, 51.00],
                            [12.10, 51.10],
                            [12.00, 51.10],
                            [12.00, 51.00],
                        ]
                    ],
                },
            ),
        ]

        for area in test_areas:
            session.add(area)
        session.commit()

        # Force reload cache for new implementation
        reload_gemeinde_cache()

        yield

        # Cleanup
        session.execute(
            delete(TblAemterCoordinaten).where(
                TblAemterCoordinaten.ags.in_([99999901, 99999902, 99999903, 1234567])
            )
        )
        session.commit()

    def test_finds_correct_administrative_area(self, session):
        """Test that the finder returns the correct area for known points."""
        test_points = [
            ((13.40, 52.52), "99999901 -- Test Berlin Mitte"),
            ((13.075, 52.40), "99999902 -- Test Potsdam"),
            ((12.05, 51.05), "01234567 -- Test Kleinstadt"),
        ]

        for point, expected in test_points:
            result = get_amt_optimized(point)
            assert result == expected, (
                f"Wrong result for point {point}: got {result}, expected {expected}"
            )

    def test_returns_none_for_outside_points(self, session):
        """Test that points outside all areas return None."""
        result = get_amt_optimized((10.0, 50.0))
        assert result is None

    def test_handles_malformed_data(self, session):
        """Test handling of malformed geometry data."""
        # Add area with malformed data
        bad_area = TblAemterCoordinaten(
            ags=88888888,
            gen="Bad Geometry Area",
            properties='{"type": "InvalidType", "coordinates": []}',  # String with invalid geometry
        )
        session.add(bad_area)
        session.commit()

        # Force cache reload
        reload_gemeinde_cache()

        # Should not crash when searching
        get_amt_optimized((13.0, 52.0))
        # Result doesn't matter, just shouldn't crash

        # Cleanup
        session.execute(
            delete(TblAemterCoordinaten).where(TblAemterCoordinaten.ags == 88888888)
        )
        session.commit()

    def test_multipolygon_support(self, session):
        """Test support for MultiPolygon geometries."""
        # Add MultiPolygon area
        multi_area = TblAemterCoordinaten(
            ags=77777777,
            gen="Multi Area",
            properties={
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [14.0, 53.0],
                            [14.1, 53.0],
                            [14.1, 53.1],
                            [14.0, 53.1],
                            [14.0, 53.0],
                        ]
                    ],
                    [
                        [
                            [14.2, 53.2],
                            [14.3, 53.2],
                            [14.3, 53.3],
                            [14.2, 53.3],
                            [14.2, 53.2],
                        ]
                    ],
                ],
            },
        )
        session.add(multi_area)
        session.commit()

        # Force cache reload
        reload_gemeinde_cache()

        # Test points in both polygons
        point1 = (14.05, 53.05)  # In first polygon
        point2 = (14.25, 53.25)  # In second polygon

        result1 = get_amt_optimized(point1)
        result2 = get_amt_optimized(point2)

        assert result1 == "77777777 -- Multi Area"
        assert result2 == "77777777 -- Multi Area"

        # Cleanup
        session.execute(
            delete(TblAemterCoordinaten).where(TblAemterCoordinaten.ags == 77777777)
        )
        session.commit()
