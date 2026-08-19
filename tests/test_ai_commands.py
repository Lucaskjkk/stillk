from __future__ import annotations

import os
from pathlib import Path

from typer.testing import CliRunner

from stillk.cli import app


runner = CliRunner()


def test_inspect_on_minimal_project(tmp_path):
    project = tmp_path / "proj"
    project.mkdir()
    # add requirements
    (project / "requirements.txt").write_text("torch\ntransformers\n")

    result = runner.invoke(app, ["inspect", str(project)])
    assert result.exit_code == 0
    assert "Frameworks:" in result.stdout


def test_doctor_reports(tmp_path):
    result = runner.invoke(app, ["doctor", str(tmp_path)])
    assert result.exit_code == 0
    assert "Python" in result.stdout


def test_clean_detects_and_removes_pycache(tmp_path):
    project = tmp_path / "proj"
    project.mkdir()
    pkg = project / "pkg"
    pkg.mkdir()
    pycache = pkg / "__pycache__"
    pycache.mkdir()
    f = pycache / "x.pyc"
    f.write_text("x")

    # dry run
    result = runner.invoke(app, ["clean", str(project)])
    assert result.exit_code == 0
    assert "Dry run" in result.stdout

    # perform removal with confirmation
    result = runner.invoke(app, ["clean", str(project), "--yes"], input="y\n")
    assert result.exit_code == 0
    assert "Removed" in result.stdout
    assert not pycache.exists()


def test_train_detects_script(tmp_path):
    project = tmp_path / "proj"
    (project / "src").mkdir(parents=True)
    train_script = project / "src" / "training.py"
    train_script.write_text("print('train')")
    result = runner.invoke(app, ["train", str(project)])
    assert result.exit_code == 0
    assert "Training script" in result.stdout


def test_eval_detects(tmp_path):
    project = tmp_path / "proj"
    (project / "src" / "evals").mkdir(parents=True)
    result = runner.invoke(app, ["eval", str(project)])
    # CLI returns exit code 0 if found, otherwise exits with 1
    assert result.exit_code == 0


def test_run_component_api_not_found(tmp_path):
    result = runner.invoke(app, ["run", "api", str(tmp_path)])
    assert result.exit_code == 1
