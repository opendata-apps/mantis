import subprocess
import pytest


@pytest.mark.style
def test_black_formatting():
    # Define paths to check
    paths_to_check = ["app", "tests", "manage.py", "run.py", "base.py "]
    formatting_issues = []

    # Run Black in check mode for each path
    for path in paths_to_check:
        result = subprocess.run(
            ["black", "--check", path], capture_output=True, text=True
        )
        if result.returncode != 0:
            # Collect the paths with formatting issues
            formatting_issues.append(
                f"Black formatting issues in {path}:\n{result.stderr}"
            )

    # If formatting issues were found, suggest a command to fix them
    if formatting_issues:
        suggestion = (
            "\nTo fix formatting issues, run: 'black " + " ".join(paths_to_check) + "'"
        )
        assert not formatting_issues, "\n\n".join(formatting_issues) + suggestion
    else:
        # Assert no formatting issues were found
        assert not formatting_issues, "\n\n".join(formatting_issues)
