"""Repair guard tests do not call Gemini or modify actual repository files."""
from pathlib import Path
import subprocess

import pytest

from automation.repair import apply_source_repair, changed_source_paths, repair_prompt


def test_source_only_repair(tmp_path):
    folder = tmp_path / "src" / "rescueflow"
    folder.mkdir(parents=True)
    path = folder / "forecast.py"
    path.write_text("value = 1\n", encoding="utf-8")
    result = apply_source_repair(
        {"files": [{"path": "src/rescueflow/forecast.py", "content": "value = 2\n"}]},
        {"src/rescueflow/forecast.py"}, tmp_path,
    )
    assert result == ["src/rescueflow/forecast.py"]
    assert path.read_text() == "value = 2\n"


def test_cannot_change_tests_or_workflows(tmp_path):
    folder = tmp_path / "src" / "rescueflow"
    folder.mkdir(parents=True)
    target = folder / "forecast.py"
    target.write_text("value = 1\n", encoding="utf-8")
    proposal = {"files": [
        {"path": "src/rescueflow/forecast.py", "content": "value = 2\n"},
        {"path": "tests/test_forecast.py", "content": "assert True\n"},
    ]}
    with pytest.raises(ValueError, match="already modified source"):
        apply_source_repair(proposal, {"src/rescueflow/forecast.py"}, tmp_path)
    assert target.read_text() == "value = 1\n"


def test_cannot_touch_unmodified_source(tmp_path):
    for name in ["src/rescueflow/forecast.py", "src/rescueflow/decisions.py"]:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x = 1\n", encoding="utf-8")
    with pytest.raises(ValueError):
        apply_source_repair(
            {"files": [{"path": "src/rescueflow/decisions.py", "content": "x = 999\n"}]},
            {"src/rescueflow/forecast.py"}, tmp_path,
        )
    assert (tmp_path / "src/rescueflow/decisions.py").read_text() == "x = 1\n"


def test_changed_source_paths_only_original_diff(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "ci@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "CI Test"], cwd=tmp_path, check=True)
    folder = tmp_path / "src" / "rescueflow"
    folder.mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    (folder / "forecast.py").write_text("x = 1\n")
    (tmp_path / "tests" / "test_forecast.py").write_text("assert True\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=tmp_path, check=True)
    (folder / "forecast.py").write_text("x = 2\n")
    (tmp_path / "tests" / "test_forecast.py").write_text("assert False\n")
    assert changed_source_paths(tmp_path) == {"src/rescueflow/forecast.py"}


def test_prompt_instructs_no_test_edits(tmp_path):
    # Test the prompt language without calling a model or requiring real files.
    p = repair_prompt(tmp_path, {"id": "test", "title": "Forecast", "instructions": "Fix interval", "acceptance": []},
                      "AssertionError", {"src/rescueflow/forecast.py"})
    assert "DO NOT change tests" in p
    assert "AssertionError" in p
