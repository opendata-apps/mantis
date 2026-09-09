"""Helpers shared by more than one admin route module."""

from typing import Any

from sqlalchemy import inspect as sa_inspect

from app.tools.location_enrichment import calculate_spatial_fields


def recalculate_amt_mtb(fundort):
    """Recalculate AMT, MTB, and fill land/kreis from spatial data."""
    if not fundort:
        return

    spatial_fields = calculate_spatial_fields(fundort.latitude, fundort.longitude)
    fundort.mtb = spatial_fields["mtb"]
    fundort.amt = spatial_fields["amt"]
    # AGS spatial data is authoritative for land/kreis.
    if spatial_fields["land"]:
        fundort.land = spatial_fields["land"]
    if spatial_fields["kreis"]:
        fundort.kreis = spatial_fields["kreis"]


def _inspect_sqlalchemy(target) -> Any:
    """Typed boundary for SQLAlchemy inspection APIs with incomplete stubs."""
    return sa_inspect(target)
