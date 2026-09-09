from pathlib import Path
import runpy
import sys

import pytest


def test_missing_input_does_not_truncate_results(tmp_path, monkeypatch):
    script = Path(__file__).resolve().parents[2] / "app/tools/check_distance.py"
    output = tmp_path / "results.txt"
    output.write_text("previous analysis\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(sys.modules, "fundorte_data", None)

    with pytest.raises(ModuleNotFoundError):
        runpy.run_path(str(script), run_name="__main__")

    assert output.read_text() == "previous analysis\n"
