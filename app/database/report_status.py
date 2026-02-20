"""
Report status enum for Mantis Tracker.

This module defines the status values for report review workflow.
Status values are 4 characters max to fit in a 5-char database column.

Statuses are divided into two categories:
- Workflow states (OPEN, APPR, DEL): Mutually exclusive primary states
- Flags (INFO, UNKL): Can be combined with workflow states
"""

from enum import StrEnum


class ReportStatus(StrEnum):
    """
    Status enum for report review workflow.

    Workflow States (mutually exclusive):
        OPEN: Report is pending review (not yet processed)
        APPR: Report has been approved/accepted
        DEL: Report has been soft-deleted (exclusive - no other statuses allowed)

    Flags (can combine with OPEN only):
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
    def get_display_names(cls, statuses: list[str]) -> str:
        """Return comma-separated German display names for multiple statuses."""
        return ", ".join(cls.get_display_name(s) for s in statuses)

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
        return [s.value for s in cls if isinstance(s.value, str)]

    @classmethod
    def validate_combination(cls, statuses: list[str]) -> tuple[bool, str | None]:
        """
        Validate that a status combination is valid.

        Rules:
        - Must have at least one status
        - DEL is exclusive (cannot combine with other statuses)
        - APPR is exclusive (approved = review complete, no active flags)
        - OPEN and APPR are mutually exclusive (can't have both)
        - INFO and UNKL can only combine with OPEN

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not statuses:
            return False, "At least one status is required"

        status_set = set(statuses)
        valid_values = set(cls.values())

        # Check all values are valid
        invalid = status_set - valid_values
        if invalid:
            return False, f"Invalid status values: {invalid}"

        # DEL is exclusive
        if cls.DEL.value in status_set and len(status_set) > 1:
            return False, "DEL status cannot be combined with other statuses"

        # APPR is exclusive (approval resolves all active concerns)
        if cls.APPR.value in status_set and len(status_set) > 1:
            return False, "APPR status cannot be combined with flags"

        # OPEN and APPR are mutually exclusive
        if cls.OPEN.value in status_set and cls.APPR.value in status_set:
            return False, "OPEN and APPR are mutually exclusive"

        # Must have exactly one workflow state (OPEN, APPR, or DEL)
        workflow_states = status_set & {cls.OPEN.value, cls.APPR.value, cls.DEL.value}
        if len(workflow_states) != 1:
            return False, "Must have exactly one workflow state (OPEN, APPR, or DEL)"

        return True, None

    @classmethod
    def get_workflow_state(cls, statuses: list[str]) -> str | None:
        """Extract the primary workflow state from a list of statuses."""
        for state in [cls.DEL.value, cls.APPR.value, cls.OPEN.value]:
            if state in statuses:
                return state
        return None
