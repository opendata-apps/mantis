"""Functional tests for gemeinde finder optimization."""
import pytest
import time
from app import db
from app.tools.find_gemeinde import get_amt_full_scan
from app.tools.gemeinde_finder import get_amt_optimized, reload_gemeinde_cache
from app.database.aemter_koordinaten import TblAemterCoordinaten


class TestGemeindeOptimization:
    """Test the optimized gemeinde finder with real database."""
    
    @pytest.fixture(autouse=True)
    def setup(self, session):
        """Setup test data."""
        self.session = session
        
        # Clear any existing test data
        session.query(TblAemterCoordinaten).filter(
            TblAemterCoordinaten.ags.in_([99999901, 99999902, 99999903])
        ).delete()
        
        # Add test administrative areas
        test_areas = [
            TblAemterCoordinaten(
                ags=99999901,
                gen="Test Berlin Mitte",
                properties={
                    "type": "Polygon",
                    "coordinates": [[
                        [13.38, 52.50],
                        [13.42, 52.50],
                        [13.42, 52.54],
                        [13.38, 52.54],
                        [13.38, 52.50]
                    ]]
                }
            ),
            TblAemterCoordinaten(
                ags=99999902,
                gen="Test Potsdam",
                properties={
                    "type": "Polygon",
                    "coordinates": [[
                        [13.00, 52.35],
                        [13.15, 52.35],
                        [13.15, 52.45],
                        [13.00, 52.45],
                        [13.00, 52.35]
                    ]]
                }
            ),
            TblAemterCoordinaten(
                ags=1234567,  # Test with AGS < 10000000
                gen="Test Kleinstadt",
                properties={
                    "type": "Polygon",
                    "coordinates": [[
                        [12.00, 51.00],
                        [12.10, 51.00],
                        [12.10, 51.10],
                        [12.00, 51.10],
                        [12.00, 51.00]
                    ]]
                }
            )
        ]
        
        for area in test_areas:
            session.add(area)
        session.commit()
        
        # Force reload cache for new implementation
        reload_gemeinde_cache()
        
        yield
        
        # Cleanup
        session.query(TblAemterCoordinaten).filter(
            TblAemterCoordinaten.ags.in_([99999901, 99999902, 99999903, 1234567])
        ).delete()
        session.commit()
    
    def test_both_implementations_return_same_result(self, session):
        """Test that both implementations return the same result."""
        test_points = [
            ((13.40, 52.52), "99999901 -- Test Berlin Mitte"),
            ((13.075, 52.40), "99999902 -- Test Potsdam"),
            ((12.05, 51.05), "01234567 -- Test Kleinstadt"),
            ((10.0, 50.0), None),  # Outside all areas
        ]
        
        for point, expected in test_points:
            # Test old implementation
            result_old = get_amt_full_scan(point)
            
            # Test new implementation
            result_new = get_amt_optimized(point)
            
            # Both should return the same result
            assert result_old == result_new, f"Results differ for point {point}: old={result_old}, new={result_new}"
            
            # And both should match expected if provided
            if expected is not None:
                assert result_old == expected, f"Old implementation wrong for {point}"
                assert result_new == expected, f"New implementation wrong for {point}"
    
    def test_performance_improvement(self, session):
        """Test that the new implementation is faster."""
        # Add more test areas to make performance difference noticeable
        for i in range(20):
            area = TblAemterCoordinaten(
                ags=90000000 + i,
                gen=f"Performance Test Area {i}",
                properties={
                    "type": "Polygon",
                    "coordinates": [[
                        [10 + i * 0.1, 48.0],
                        [10 + (i + 1) * 0.1, 48.0],
                        [10 + (i + 1) * 0.1, 49.0],
                        [10 + i * 0.1, 49.0],
                        [10 + i * 0.1, 48.0]
                    ]]
                }
            )
            session.add(area)
        session.commit()
        
        # Force cache reload
        reload_gemeinde_cache()
        
        # Test point in one of the areas
        test_point = (11.05, 48.5)
        
        # Time old implementation (10 calls)
        start = time.time()
        for _ in range(10):
            get_amt_full_scan(test_point)
        time_old = time.time() - start
        
        # Time new implementation (10 calls)
        # First call loads cache, subsequent calls use cache
        start = time.time()
        for _ in range(10):
            get_amt_optimized(test_point)
        time_new = time.time() - start
        
        # New should be faster
        print(f"Old implementation: {time_old:.4f}s for 10 calls")
        print(f"New implementation: {time_new:.4f}s for 10 calls")
        print(f"Speedup: {time_old/time_new:.2f}x")
        
        # New implementation should be at least 2x faster
        assert time_new < time_old * 0.5, f"New implementation not fast enough: {time_new}s vs {time_old}s"
        
        # Cleanup performance test data
        session.query(TblAemterCoordinaten).filter(
            TblAemterCoordinaten.ags >= 90000000
        ).delete()
        session.commit()
    
    def test_handles_malformed_data(self, session):
        """Test handling of malformed geometry data."""
        # Add area with malformed data
        bad_area = TblAemterCoordinaten(
            ags=88888888,
            gen="Bad Geometry Area",
            properties='{"type": "InvalidType", "coordinates": []}'  # String with invalid geometry
        )
        session.add(bad_area)
        session.commit()
        
        # Force cache reload
        reload_gemeinde_cache()
        
        # Should not crash when searching
        result = get_amt_optimized((13.0, 52.0))
        # Result doesn't matter, just shouldn't crash
        
        # Cleanup
        session.query(TblAemterCoordinaten).filter_by(ags=88888888).delete()
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
                    [[[14.0, 53.0], [14.1, 53.0], [14.1, 53.1], [14.0, 53.1], [14.0, 53.0]]],
                    [[[14.2, 53.2], [14.3, 53.2], [14.3, 53.3], [14.2, 53.3], [14.2, 53.2]]]
                ]
            }
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
        session.query(TblAemterCoordinaten).filter_by(ags=77777777).delete()
        session.commit()