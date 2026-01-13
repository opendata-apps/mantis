"""
Report status enum for Mantis Tracker.

This module defines the status values for report review workflow.
Status values are 4 characters max to fit in a 5-char database column.
"""

from enum import StrEnum


class ReportStatus(StrEnum):
    """
    Status enum for report review workflow.

    Values:
        OPEN: Report is pending review (not yet processed)
        APPR: Report has been approved/accepted
        DEL: Report has been soft-deleted
        INFO: Reporter has been contacted for more information
        UNKL: Report is unclear and needs investigation
    """

    OPEN = "OPEN"  # Offen - awaiting review
    APPR = "APPR"  # Angenommen/Bearbeitet - approved
    DEL = "DEL"  # Gelöscht - deleted
    INFO = "INFO"  # Informiert - contacted reporter for info
    UNKL = "UNKL"  # Unklar - unclear, needs investigation

    @classmethod
    def get_display_name(cls, status: str) -> str:
        """Return German display name for status."""
        display_names = {
            cls.OPEN.value: "Offen",
            cls.APPR.value: "Angenommen",
            cls.DEL.value: "Gelöscht",
            cls.INFO.value: "Informiert",
            cls.UNKL.value: "Unklar",
        }
        return display_names.get(status, status)

    @classmethod
    def get_css_class(cls, status: str) -> str:
        """Return Tailwind CSS classes for status badge."""
        css_classes = {
            cls.OPEN.value: "bg-gray-100 text-gray-800",
            cls.APPR.value: "bg-green-100 text-gray-800",
            cls.DEL.value: "bg-red-500/80 text-gray-800",
            cls.INFO.value: "bg-yellow-100 text-yellow-800",
            cls.UNKL.value: "bg-orange-100 text-orange-800",
        }
        return css_classes.get(status, "bg-gray-100 text-gray-800")

    @classmethod
    def values(cls) -> list[str]:
        """Return list of all status values."""
        return [s.value for s in cls]
