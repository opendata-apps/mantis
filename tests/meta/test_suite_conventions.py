"""Conventions this suite enforces on itself.

Three defects that a green test run cannot reveal, because the test passes
either way. Each is found by parsing the test sources, the same approach
``tests/migrations/test_migration_chain.py`` uses on migration scripts.

The rules come from Google's "Test Behavior, Not Implementation" and the
testing chapter of *Software Engineering at Google*; ``docs/develop/testing.rst``
states them in full.

Every rule carries the offenders that existed when it was introduced. The
baseline is checked in both directions: fixing a test without striking it from
the list fails just as loudly as adding a new offender, so the lists can only
shrink.
"""

import ast
import collections
import pathlib

TESTS = pathlib.Path(__file__).parents[1]

# Replacing these in a test says nothing about our code, so asserting that they
# were called is a statement about behaviour, not about implementation.
EXTERNAL_BOUNDARIES = ("mail.send", "requests.", "subprocess.")

MOCK_ASSERTIONS = {
    "assert_called",
    "assert_called_once",
    "assert_called_with",
    "assert_called_once_with",
    "assert_not_called",
    "assert_any_call",
    "assert_has_calls",
    "call_count",
}

# A test whose every assertion sits inside a loop or a branch passes when the
# collection is empty — an endpoint that returns nothing at all looks correct.
ASSERTIONS_ONLY_REACHED_CONDITIONALLY = {
    "tests/config/test_application_context.py::test_writable_directories_are_temporary",
    "tests/database/test_report_status.py::test_returns_strings",
    "tests/functional/test_admin_routes.py::test_pagination_on_reviewer_page",
    "tests/functional/test_coordinate_updates.py::test_update_invalid_latitude",
    "tests/functional/test_coordinate_updates.py::test_update_invalid_longitude",
    "tests/functional/test_coordinate_updates.py::test_coordinate_update_outside_germany_is_allowed",
    "tests/functional/test_coordinate_updates.py::test_coordinate_format_normalization",
    "tests/functional/test_gemeinde_optimization.py::test_finds_correct_administrative_area",
    "tests/functional/test_id_consistency.py::test_id_display_format_consistency",
    "tests/functional/test_is_comparison_filters.py::test_open_filter_query",
    "tests/functional/test_is_comparison_filters.py::test_approved_filter_query",
    "tests/functional/test_is_comparison_filters.py::test_deleted_filter_query",
    "tests/functional/test_is_comparison_filters.py::test_unspecified_gender_filter",
    "tests/functional/test_is_comparison_filters.py::test_combined_status_and_type_filters",
    "tests/functional/test_is_comparison_filters.py::test_default_filter_behavior",
    "tests/functional/test_is_comparison_filters.py::test_status_field_edge_cases",
    "tests/functional/test_rate_limits.py::test_authenticated_reviewer_navigation_is_not_throttled",
    "tests/functional/test_security_headers.py::test_responses_prevent_referrer_disclosure",
    "tests/migrations/test_migration_chain.py::test_linear_chain",
    "tests/migrations/test_migration_chain.py::test_has_downgrade",
    "tests/statistics/test_ags_reference.py::test_codes_are_two_digits",
    "tests/statistics/test_ags_reference.py::test_no_invisible_unicode",
    "tests/statistics/test_ags_reference.py::test_codes_start_with_11",
    "tests/statistics/test_ags_reference.py::test_codes_are_eight_digits",
    "tests/statistics/test_ags_reference.py::test_codes_start_with_12",
    "tests/statistics/test_ags_reference.py::test_codes_are_five_digits",
    "tests/statistics/test_ags_reference.py::test_contains_all_states",
    "tests/statistics/test_ags_reference.py::test_contains_all_brandenburg_landkreise",
    "tests/statistics/test_ags_reference.py::test_state_entries_have_correct_structure",
    "tests/statistics/test_ags_reference.py::test_district_entries_have_correct_structure",
    "tests/unit/test_coordinate_validation.py::test_validate_latitude_valid",
    "tests/unit/test_coordinate_validation.py::test_validate_latitude_invalid",
    "tests/unit/test_coordinate_validation.py::test_validate_longitude_valid",
    "tests/unit/test_coordinate_validation.py::test_validate_longitude_invalid",
    "tests/unit/test_coordinate_validation.py::test_swapped_pairs_detected",
    "tests/unit/test_coordinate_validation.py::test_correct_pairs_not_flagged",
    "tests/unit/test_coordinate_validation.py::test_nan_and_inf_rejected",
    "tests/unit/test_fetch_ags.py::test_merge_normalizes_all_properties",
    "tests/unit/test_report_helpers.py::test_exactly_one_flag_set_for_known_values",
}

# Two tests of the same name in one file: the name no longer identifies the case
# it covers, and neither does the failure report.
REUSED_NAMES = {
    "tests/database/test_meldungen_status_properties.py::test_false_when_open",
    "tests/database/test_meldungen_status_properties.py::test_false_when_approved",
    "tests/functional/test_coordinate_updates.py::test_update_coordinates_nonexistent_sighting",
    "tests/tools/test_check_reviewer.py::test_preserves_function_attributes",
    "tests/tools/test_check_reviewer.py::test_deleted_user_gets_403",
    "tests/tools/test_check_reviewer.py::test_exposes_current_user",
    "tests/unit/test_report_helpers.py::test_empty_string",
    "tests/unit/test_report_helpers.py::test_both_empty",
    "tests/unit/test_report_helpers.py::test_known_values",
    "tests/unit/test_report_helpers.py::test_empty",
}

# Replacing one of our own functions and then asserting it was called restates
# the code under test. Assert on the response or on what was saved instead.
ASSERTS_CALLS_ON_OUR_OWN_CODE = {
    "tests/database/test_populate_functions.py::test_populate_all_success",
    "tests/database/test_populate_functions.py::test_populate_all_beschreibung_error_stops_pipeline",
    "tests/database/test_populate_functions.py::test_populate_all_swallows_import_error",
    "tests/database/test_populate_functions.py::test_populate_all_skips_aemter_when_no_data",
    "tests/functional/test_admin_approval.py::test_toggle_approve_sighting",
    "tests/functional/test_backup_routes.py::test_backup_route_creates_backup_and_sends_mail",
    "tests/functional/test_report_routes.py::test_successful_submission",
    "tests/functional/test_report_submission.py::test_submission_outside_germany_is_allowed",
}


def _test_functions():
    """Every collected test function, as (id, file-relative path, ast node)."""
    for path in sorted(TESTS.rglob("test_*.py")):
        relative = path.relative_to(TESTS.parent).as_posix()
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            if not node.name.startswith("test_"):
                continue
            if any("fixture" in ast.unparse(d) for d in node.decorator_list):
                continue
            yield f"{relative}::{node.name}", relative, node


def _asserts(node):
    return [n for n in ast.walk(node) if isinstance(n, ast.Assert)]


def _patch_targets(node):
    """Strings handed to ``patch(...)`` in the body or the decorators."""
    sources = [node, *(ast.Expression(d) for d in node.decorator_list)]
    for source in sources:
        for call in ast.walk(source):
            if not isinstance(call, ast.Call):
                continue
            name = ast.unparse(call.func)
            if name != "patch" and not name.endswith((".patch", "patch.object")):
                continue
            for argument in call.args[:1]:
                if isinstance(argument, ast.Constant) and isinstance(
                    argument.value, str
                ):
                    yield argument.value


def _compare(found, baseline, added, fixed):
    """One assertion per direction, so the baseline can only shrink."""
    new_offenders = sorted(found - baseline)
    assert not new_offenders, added.format(tests="\n  ".join(new_offenders))

    no_longer_offenders = sorted(baseline - found)
    assert not no_longer_offenders, fixed.format(tests="\n  ".join(no_longer_offenders))


def test_every_test_asserts_something_unconditionally():
    """A loop over an empty result must not look like a passing test."""
    found = set()
    for test_id, _, node in _test_functions():
        asserts = _asserts(node)
        if not asserts:
            continue  # proves its point by not raising; that is a valid test
        conditional = set()
        for statement in ast.walk(node):
            if isinstance(statement, (ast.For, ast.While, ast.If)):
                conditional |= {id(a) for a in _asserts(statement)}
        if all(id(a) in conditional for a in asserts):
            found.add(test_id)

    _compare(
        found,
        ASSERTIONS_ONLY_REACHED_CONDITIONALLY,
        "Every assertion in these tests sits inside a loop or a branch, so they "
        "pass when the collection is empty. Assert on the whole result — "
        "`assert ids == {{8, 18}}` — or use @pytest.mark.parametrize:\n  {tests}",
        "These tests now assert unconditionally. Strike them from "
        "ASSERTIONS_ONLY_REACHED_CONDITIONALLY:\n  {tests}",
    )


def test_test_names_are_unique_within_their_file():
    """The name is how a failure report identifies the case."""
    counts = collections.defaultdict(collections.Counter)
    for _, relative, node in _test_functions():
        counts[relative][node.name] += 1
    found = {
        f"{relative}::{name}"
        for relative, names in counts.items()
        for name, seen in names.items()
        if seen > 1
    }

    _compare(
        found,
        REUSED_NAMES,
        "These names are used by more than one test in the same file, so a "
        "failure does not say which case broke:\n  {tests}",
        "These names are unique again. Strike them from REUSED_NAMES:\n  {tests}",
    )


def test_no_test_asserts_that_our_own_function_was_called():
    """State testing over interaction testing, outside the process boundary."""
    found = set()
    for test_id, _, node in _test_functions():
        body = ast.walk(node)
        asserted = {
            n.attr
            for n in body
            if isinstance(n, ast.Attribute) and n.attr in MOCK_ASSERTIONS
        }
        if not asserted:
            continue
        ours = [
            target
            for target in _patch_targets(node)
            if target.startswith("app.")
            and not any(boundary in target for boundary in EXTERNAL_BOUNDARIES)
        ]
        if ours:
            found.add(test_id)

    _compare(
        found,
        ASSERTS_CALLS_ON_OUR_OWN_CODE,
        "These tests replace one of our own functions and then assert it was "
        "called, which restates the code instead of testing it. Assert on the "
        "response or on what was saved; mock only at the process boundary "
        f"({', '.join(EXTERNAL_BOUNDARIES)}):\n  {{tests}}",
        "These tests no longer assert on their own calls. Strike them from "
        "ASSERTS_CALLS_ON_OUR_OWN_CODE:\n  {tests}",
    )
