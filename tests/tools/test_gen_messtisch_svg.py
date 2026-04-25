"""Tests for the Messtischblatt SVG generator.

The generator renders a German TK25 grid (rows 24-46, columns 33-54 by default)
with data points drawn as filled circles labelled with their count. The function
uses ``flask.url_for`` to compose the background image href, so it requires an
active Flask request context — which the ``request_context`` fixture provides.
"""

import re

import pytest

from app.tools.gen_messtisch_svg import create_measure_sheet


pytestmark = pytest.mark.usefixtures("request_context")


class TestEmptyDataset:
    def test_returns_svg_string(self):
        svg = create_measure_sheet(dataset=[])
        assert isinstance(svg, str)
        assert svg.startswith("<?xml") or "<svg" in svg

    def test_no_circles_drawn(self):
        svg = create_measure_sheet(dataset=[])
        assert "<circle" not in svg

    def test_contains_background_image(self):
        svg = create_measure_sheet(dataset=[])
        assert "land_brandenburg.svg" in svg

    def test_none_dataset_renders_grid_without_circles(self):
        svg = create_measure_sheet(dataset=None)
        assert "<circle" not in svg
        assert "<svg" in svg


class TestPopulatedDataset:
    def test_single_point_draws_one_circle(self):
        svg = create_measure_sheet(dataset=[(3328, 5)])
        # svgwrite renders <circle .../>; count occurrences
        assert svg.count("<circle") == 1

    def test_multiple_points_draws_multiple_circles(self):
        svg = create_measure_sheet(dataset=[(3328, 5), (3830, 10), (4634, 99)])
        assert svg.count("<circle") == 3

    def test_counts_rendered_as_text_labels(self):
        svg = create_measure_sheet(dataset=[(3328, 5), (4634, 99)])
        # Each count is wrapped as SVG text content
        assert ">5</text>" in svg
        assert ">99</text>" in svg

    def test_axis_labels_rendered_for_default_range(self):
        svg = create_measure_sheet(dataset=[])
        # Default row_range=(24, 46): the ends should appear as row labels
        assert ">24</text>" in svg
        assert ">46</text>" in svg
        # Default col_range=(33, 54)
        assert ">33</text>" in svg
        assert ">54</text>" in svg


class TestMarkerPlacement:
    """Regression tests for issue #173: markers must land on the correct grid cell.

    For MTB number RRCC, *(coord % 100)* is the column (W->E, x-axis) and
    *(coord // 100)* is the row (N->S, y-axis). With default ranges
    (rows 24-46, cols 33-54) and box_size=50, the marker must be drawn at:
        cx = (CC - 33 + 1.5) * 50
        cy = (RR - 24 + 1.5) * 50
    """

    @staticmethod
    def _circle_centers(svg):
        return [
            (float(cx), float(cy))
            for cx, cy in re.findall(
                r'<circle[^>]*cx="([\d.]+)"[^>]*cy="([\d.]+)"', svg
            )
        ]

    def test_herzberg_mtb_4245_lands_on_brandenburg(self):
        # MTB 4245 = Herzberg (Elster), Brandenburg.
        # Expected pixel center with defaults: cx = (45-33+1.5)*50 = 675,
        # cy = (42-24+1.5)*50 = 975.
        svg = create_measure_sheet(dataset=[(4245, 1)])
        assert (675.0, 975.0) in self._circle_centers(svg)

    def test_marker_uses_col_for_x_and_row_for_y(self):
        # Two MTBs with the same row but different cols should differ in cx, share cy.
        svg = create_measure_sheet(dataset=[(4245, 1), (4250, 2)])
        centers = self._circle_centers(svg)
        assert len(centers) == 2
        cx1, cy1 = centers[0]
        cx2, cy2 = centers[1]
        assert cy1 == cy2  # same row -> same vertical position
        assert cx2 - cx1 == (50 - 45) * 50  # 5 columns east


class TestCustomRanges:
    def test_custom_box_size_scales_output(self):
        svg_small = create_measure_sheet(box_size=25, dataset=[])
        svg_large = create_measure_sheet(box_size=100, dataset=[])
        # Pull width from the SVG root
        w_small = int(re.search(r'width="(\d+)px"', svg_small).group(1))
        w_large = int(re.search(r'width="(\d+)px"', svg_large).group(1))
        assert w_large == w_small * 4

    def test_custom_ranges_change_dimensions(self):
        svg_default = create_measure_sheet(dataset=[])
        svg_narrow = create_measure_sheet(
            row_range=(30, 40), col_range=(40, 50), dataset=[]
        )
        w_default = int(re.search(r'width="(\d+)px"', svg_default).group(1))
        w_narrow = int(re.search(r'width="(\d+)px"', svg_narrow).group(1))
        assert w_narrow < w_default
