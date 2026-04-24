"""Unit tests for the WFS fetch helpers in ``app/tools/fetch_ags.py``.

These verify that the low-level ``_wfs_get_feature`` call builds the
correct query string and that the three public fetchers dispatch to the
right typename. ``requests.get`` is mocked so no network traffic occurs.
"""

from unittest.mock import Mock, patch

import pytest

from app.tools import fetch_ags


def _mock_response(payload):
    resp = Mock()
    resp.json.return_value = payload
    resp.raise_for_status = Mock()
    return resp


class TestFetchGemeinden:
    def test_calls_bkg_wfs_with_gemeinden_typename(self):
        payload = {
            "type": "FeatureCollection",
            "numberReturned": 2,
            "features": [{}, {}],
        }
        with patch(
            "app.tools.fetch_ags.requests.get", return_value=_mock_response(payload)
        ) as mock_get:
            data = fetch_ags.fetch_gemeinden()

        assert data == payload
        # The first positional arg is the URL; query params travel in ``params``
        (url,) = mock_get.call_args.args
        assert url == fetch_ags.BKG_WFS_BASE
        assert mock_get.call_args.kwargs["params"]["typenames"] == (
            "vg5000_0101:vg5000_gem"
        )


class TestFetchKreise:
    def test_calls_bkg_wfs_with_kreise_typename(self):
        payload = {"type": "FeatureCollection", "features": []}
        with patch(
            "app.tools.fetch_ags.requests.get", return_value=_mock_response(payload)
        ) as mock_get:
            data = fetch_ags.fetch_kreise()

        assert data == payload
        assert mock_get.call_args.kwargs["params"]["typenames"] == (
            "vg5000_0101:vg5000_krs"
        )

    def test_count_falls_back_to_feature_length(self):
        """When the WFS response lacks ``numberReturned`` the helper logs
        ``len(features)`` instead. This guards against a noisy
        ``KeyError`` that would break the seed-ags command."""
        payload = {"type": "FeatureCollection", "features": [{}, {}, {}]}
        with patch(
            "app.tools.fetch_ags.requests.get", return_value=_mock_response(payload)
        ):
            data = fetch_ags.fetch_kreise()
        assert len(data["features"]) == 3


class TestFetchBerlinBezirke:
    def test_returns_features_list_not_feature_collection(self):
        payload = {
            "type": "FeatureCollection",
            "features": [
                {"properties": {"name": "11000001", "namgem": "Mitte"}},
                {"properties": {"name": "11000002", "namgem": "Friedrichshain"}},
            ],
        }
        with patch(
            "app.tools.fetch_ags.requests.get", return_value=_mock_response(payload)
        ) as mock_get:
            features = fetch_ags.fetch_berlin_bezirke()

        assert isinstance(features, list)
        assert len(features) == 2
        assert features[0]["properties"]["namgem"] == "Mitte"
        # Routed to Berlin's WFS endpoint
        (url,) = mock_get.call_args.args
        assert url == fetch_ags.BERLIN_WFS_BASE


class TestWfsGetFeatureParams:
    """Direct tests of the private ``_wfs_get_feature`` helper — verify
    that query params are assembled correctly and that ``extra_params``
    can override or extend them."""

    def test_default_srs_is_epsg_4326(self):
        with patch(
            "app.tools.fetch_ags.requests.get",
            return_value=_mock_response({"type": "FeatureCollection"}),
        ) as mock_get:
            fetch_ags._wfs_get_feature(fetch_ags.BKG_WFS_BASE, "some:typename")
        assert mock_get.call_args.kwargs["params"]["srsName"] == "EPSG:4326"

    def test_extra_params_merged(self):
        with patch(
            "app.tools.fetch_ags.requests.get",
            return_value=_mock_response({"type": "FeatureCollection"}),
        ) as mock_get:
            fetch_ags._wfs_get_feature(
                fetch_ags.BKG_WFS_BASE,
                "some:typename",
                extra_params={"count": "100"},
            )
        params = mock_get.call_args.kwargs["params"]
        assert params["count"] == "100"
        assert params["typenames"] == "some:typename"

    def test_raises_on_http_error(self):
        bad = Mock()
        bad.raise_for_status.side_effect = RuntimeError("502 Bad Gateway")

        with patch("app.tools.fetch_ags.requests.get", return_value=bad):
            with pytest.raises(RuntimeError, match="502"):
                fetch_ags._wfs_get_feature(fetch_ags.BKG_WFS_BASE, "some:typename")
