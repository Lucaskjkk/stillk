from __future__ import annotations

from typer.testing import CliRunner

from stillk.cli import app


runner = CliRunner()


def test_init_ml_template(tmp_path):
    result = runner.invoke(
        app,
        [
            "init",
            "demo-ml",
            "--project-type",
            "ml",
            "--framework",
            "scikit-learn",
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.stdout

    project_dir = tmp_path / "demo-ml"
    assert project_dir.exists()
    assert (project_dir / "pyproject.toml").exists()
    assert (project_dir / "README.md").exists()
    assert (project_dir / "src" / "training" / "train.py").exists()
    assert (project_dir / "src" / "inference" / "predict.py").exists()
    assert (project_dir / "data" / "raw").exists()
    assert (project_dir / "scripts" / "run_training.sh").exists()


def test_init_llm_template_generates_llm_dirs(tmp_path):
    result = runner.invoke(
        app,
        [
            "init",
            "demo-llm",
            "--project-type",
            "llm",
            "--framework",
            "transformers",
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.stdout

    project_dir = tmp_path / "demo-llm"
    assert (project_dir / "src" / "agents").exists()
    assert (project_dir / "src" / "prompts").exists()
    assert (project_dir / "src" / "retrieval").exists()
    assert (project_dir / "src" / "graph").exists()
    assert (project_dir / "src" / "evals").exists()
    assert (project_dir / "README.md").exists()
    assert (project_dir / "configs" / "model.yaml").exists()


def test_list_templates():
    result = runner.invoke(app, ["list-templates"])
    assert result.exit_code == 0, result.stdout
    assert "ml" in result.stdout
    assert "llm" in result.stdout
