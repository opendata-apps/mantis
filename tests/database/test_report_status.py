"""Tests for ReportStatus enum — workflow validation, display, and CSS mapping.

ReportStatus enforces a state machine:
- Workflow states (OPEN, APPR, DEL) are mutually exclusive
- Flags (INFO, UNKL) combine only with OPEN
- DEL and APPR are terminal/exclusive (no flags allowed)
"""

import pytest
from app.database.report_status import ReportStatus


# ---------------------------------------------------------------------------
# validate_combination — the core business rule
# ---------------------------------------------------------------------------
class TestValidateCombination:
    """Every legal and illegal status combination the workflow allows."""

    # --- Happy path: valid combinations ---

    @pytest.mark.parametrize(
        "statuses",
        [
            [ReportStatus.OPEN.value],
            [ReportStatus.APPR.value],
            [ReportStatus.DEL.value],
        ],
        ids=["open-only", "approved-only", "deleted-only"],
    )
    def test_single_workflow_state_is_valid(self, statuses):
        valid, error = ReportStatus.validate_combination(statuses)
        assert valid is True
        assert error is None

    def test_open_with_info_flag(self):
        valid, error = ReportStatus.validate_combination(["OPEN", "INFO"])
        assert valid is True
        assert error is None

    def test_open_with_unkl_flag(self):
        valid, error = ReportStatus.validate_combination(["OPEN", "UNKL"])
        assert valid is True
        assert error is None

    def test_open_with_both_flags(self):
        valid, error = ReportStatus.validate_combination(["OPEN", "INFO", "UNKL"])
        assert valid is True
        assert error is None

    # --- Unhappy path: invalid combinations ---

    def test_empty_list_rejected(self):
        valid, error = ReportStatus.validate_combination([])
        assert valid is False
        assert "at least one" in error.lower()

    def test_invalid_status_value_rejected(self):
        valid, error = ReportStatus.validate_combination(["BOGUS"])
        assert valid is False
        assert "invalid" in error.lower()

    def test_del_cannot_combine_with_open(self):
        valid, error = ReportStatus.validate_combination(["DEL", "OPEN"])
        assert valid is False

    def test_del_cannot_combine_with_info(self):
        valid, error = ReportStatus.validate_combination(["DEL", "INFO"])
        assert valid is False

    def test_del_cannot_combine_with_unkl(self):
        valid, error = ReportStatus.validate_combination(["DEL", "UNKL"])
        assert valid is False

    def test_appr_cannot_combine_with_info(self):
        valid, error = ReportStatus.validate_combination(["APPR", "INFO"])
        assert valid is False

    def test_appr_cannot_combine_with_unkl(self):
        valid, error = ReportStatus.validate_combination(["APPR", "UNKL"])
        assert valid is False

    def test_open_and_appr_mutually_exclusive(self):
        valid, error = ReportStatus.validate_combination(["OPEN", "APPR"])
        assert valid is False

    def test_flags_without_workflow_state_rejected(self):
        """INFO alone is not a valid state — needs OPEN."""
        valid, error = ReportStatus.validate_combination(["INFO"])
        assert valid is False

    def test_unkl_alone_rejected(self):
        valid, error = ReportStatus.validate_combination(["UNKL"])
        assert valid is False

    def test_flags_only_rejected(self):
        valid, error = ReportStatus.validate_combination(["INFO", "UNKL"])
        assert valid is False


# ---------------------------------------------------------------------------
# get_workflow_state — priority-based extraction
# ---------------------------------------------------------------------------
class TestGetWorkflowState:
    def test_del_takes_highest_priority(self):
        assert ReportStatus.get_workflow_state(["DEL"]) == "DEL"

    def test_appr_returned(self):
        assert ReportStatus.get_workflow_state(["APPR"]) == "APPR"

    def test_open_returned(self):
        assert ReportStatus.get_workflow_state(["OPEN"]) == "OPEN"

    def test_open_with_flags_returns_open(self):
        assert ReportStatus.get_workflow_state(["OPEN", "INFO", "UNKL"]) == "OPEN"

    def test_empty_list_returns_none(self):
        assert ReportStatus.get_workflow_state([]) is None

    def test_flags_only_returns_none(self):
        assert ReportStatus.get_workflow_state(["INFO", "UNKL"]) is None


# ---------------------------------------------------------------------------
# get_display_name / get_display_names — German labels
# ---------------------------------------------------------------------------
class TestDisplayNames:
    @pytest.mark.parametrize(
        "status, expected",
        [
            ("OPEN", "Offen"),
            ("APPR", "Angenommen"),
            ("DEL", "Gelöscht"),
            ("INFO", "Informiert"),
            ("UNKL", "Unklar"),
        ],
    )
    def test_known_status_display_name(self, status, expected):
        assert ReportStatus.get_display_name(status) == expected

    def test_unknown_status_returns_raw_value(self):
        assert ReportStatus.get_display_name("NOPE") == "NOPE"

    def test_display_names_joins_multiple(self):
        result = ReportStatus.get_display_names(["OPEN", "INFO"])
        assert result == "Offen, Informiert"

    def test_display_names_single(self):
        result = ReportStatus.get_display_names(["APPR"])
        assert result == "Angenommen"

    def test_display_names_empty(self):
        assert ReportStatus.get_display_names([]) == ""


# ---------------------------------------------------------------------------
# values — enum listing
# ---------------------------------------------------------------------------
class TestValues:
    def test_returns_all_five_statuses(self):
        vals = ReportStatus.values()
        assert set(vals) == {"OPEN", "APPR", "DEL", "INFO", "UNKL"}

    def test_returns_strings(self):
        for v in ReportStatus.values():
            assert isinstance(v, str)
