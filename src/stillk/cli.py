from __future__ import annotations

from pathlib import Path

import typer

from .core.models import ProjectConfig
from .core.registry import PROJECT_TYPES, get_framework, get_project_type
from .generator import ProjectGenerator
from .commands.tooling import (
    inspect_project,
    run_doctor,
    clean_project,
    train as tooling_train,
    evaluate as tooling_evaluate,
    benchmark as tooling_benchmark,
    run_component,
)

app = typer.Typer(help="Stillk: scaffold ML, DL, LLM, RAG and AI Agent projects.")


def _prompt_project_type() -> str:
    choices = ", ".join(f"{key} ({data.label})" for key, data in PROJECT_TYPES.items())
    return typer.prompt("Select the project type", default="ml", show_default=True, prompt_suffix=f" [{choices}] ")


def _prompt_framework(project_type_key: str) -> str:
    project_type = get_project_type(project_type_key)
    options = ", ".join(fw.key for fw in project_type.frameworks)
    default = project_type.default_framework.key if project_type.default_framework else project_type.frameworks[0].key
    return typer.prompt("Select the framework", default=default, show_default=True, prompt_suffix=f" [{options}] ")


@app.command()
def init(
    project_name: str | None = typer.Argument(None, help="Name of the project to create."),
    project_type: str = typer.Option(None, "--project-type", "-t", help="Project category: ml, dl, llm, rag, agents."),
    framework: str = typer.Option(None, "--framework", "-f", help="Framework to use for the project."),
    output_dir: str = typer.Option(".", "--output-dir", "-o", help="Folder where the project will be created."),
    author: str = typer.Option("Your Name", "--author", help="Author name used in the generated files."),
    email: str = typer.Option("your.email@example.com", "--email", help="Author contact email."),
    description: str = typer.Option("", "--description", help="Project description."),
) -> None:
    """Generate a full starter project skeleton."""
    if project_name is None:
        project_name = typer.prompt("Project name")

    project_type_key = project_type or _prompt_project_type()
    if project_type_key not in PROJECT_TYPES:
        try:
            project_type_def = get_project_type(project_type_key)
        except ValueError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc
    else:
        project_type_def = get_project_type(project_type_key)

    selected_framework = framework or _prompt_framework(project_type_key)

    try:
        get_framework(project_type_def, selected_framework)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    config = ProjectConfig(
        project_name=project_name,
        project_type=project_type_key,
        framework=selected_framework,
        author=author,
        email=email,
        description=description,
        include_rag=project_type_key in {"rag", "llm"},
        include_agents=project_type_key in {"agents", "llm"},
    )

    generator = ProjectGenerator(Path(output_dir))
    project_dir = generator.generate(config)
    typer.echo(f"Project '{config.project_name}' generated successfully at: {project_dir}")


@app.command()
def add(component: str = typer.Argument(..., help="Component to add, such as mlflow, rag, fastapi.")) -> None:
    """Add a component to an existing project. This is a future extension point for Stillk."""
    supported = {"mlflow": "MLflow integration", "rag": "RAG module", "fastapi": "FastAPI service"}
    if component not in supported:
        typer.echo(f"Component '{component}' is not supported yet. Supported: {', '.join(sorted(supported))}", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"Component '{component}' planned: {supported[component]}.")
    typer.echo("This extension is reserved for future v0.2+ features.")


@app.command()
def list_templates() -> None:
    """List all supported project types and frameworks."""
    for key, template in PROJECT_TYPES.items():
        frameworks = ", ".join(fw.label for fw in template.frameworks)
        typer.echo(f"- {key}: {template.label} ({frameworks})")


@app.command()
def inspect(path: str = typer.Argument(".", help="Path to the project root.")) -> None:
    """Inspect the current project and surface AI-related info and warnings."""
    info = inspect_project(path)
    typer.echo("Project inspection summary:")
    typer.echo(f"- Python: {info.get('python')}")
    typer.echo(f"- Frameworks: {', '.join(info.get('frameworks') or []) or 'None detected'}")
    typer.echo(f"- Has src: {info.get('has_src')}")
    typer.echo(f"- Dockerfile: {info.get('dockerfile')}")
    typer.echo(f"- GPU available: {info.get('gpu')}")
    if info.get("warnings"):
        typer.echo("\nWarnings:")
        for w in info.get("warnings", []):
            typer.secho(f"- {w}", fg=typer.colors.YELLOW)


@app.command()
def doctor(path: str = typer.Argument(".", help="Path to check.")) -> None:
    """Run quick environment checks and report OK/WARNING/ERROR."""
    results = run_doctor(path)
    for name, status in results:
        if status.startswith("OK"):
            typer.secho(f"{name}: {status}", fg=typer.colors.GREEN)
        elif status in {"WARNING", "UNKNOWN"}:
            typer.secho(f"{name}: {status}", fg=typer.colors.YELLOW)
        else:
            typer.secho(f"{name}: {status}", fg=typer.colors.RED)


@app.command()
def clean(path: str = typer.Argument(".", help="Project root path."), all: bool = typer.Option(False, "--all", help="Include all caches."), yes: bool = typer.Option(False, "--yes", help="Confirm deletion without prompting.")) -> None:
    """Detect and clean caches and temporary artifacts related to AI development."""
    info = clean_project(path, all=all, yes=yes)
    if info.get("dry_run"):
        typer.echo("Dry run - the following targets would be removed:")
        for t in info.get("targets", []):
            typer.echo(f"- {t}")
        typer.echo(f"Total size: {info.get('size')} bytes")
        typer.echo("Run again with '--yes' to actually remove these files.")
    else:
        typer.echo(f"Removed: {len(info.get('removed', []))} items. Freed {info.get('size')} bytes")


@app.command()
def train(path: str = typer.Argument(".", help="Project root path."), execute: bool = typer.Option(False, "--execute", help="Execute the detected training script."), epochs: int | None = typer.Option(None, "--epochs", help="Override epochs."), config: str | None = typer.Option(None, "--config", help="Configuration profile to use.")) -> None:
    """Detect and run training pipelines."""
    extra = []
    if epochs is not None:
        extra += ["--epochs", str(epochs)]
    if config:
        extra += ["--config", config]
    result = tooling_train(path, execute, extra)
    if not result.get("found"):
        typer.secho("No training script found.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)
    typer.echo(f"Training script: {result.get('script')}")
    typer.echo(f"Status: {result.get('status')}")


@app.command()
def eval(path: str = typer.Argument(".", help="Project root path.")) -> None:
    """Run evaluation pipelines and report metrics."""
    result = tooling_evaluate(path)
    if not result.get("found"):
        typer.secho("No evaluation pipeline found.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)
    typer.echo("Evaluation results:")
    for k, v in result.get("metrics", {}).items():
        typer.echo(f"- {k}: {v}")


@app.command()
def benchmark(path: str = typer.Argument(".", help="Project root path.")) -> None:
    """Run lightweight benchmarks between models or configurations."""
    result = tooling_benchmark(path)
    typer.echo(f"Benchmark status: {result.get('status')}")


@app.command()
def run(component: str = typer.Argument(..., help="Component to run: api, training, inference."), path: str = typer.Argument(".", help="Project root path.")) -> None:
    """Run a specific project component (api, training, inference)."""
    result = run_component(path, component)
    if not result.get("found"):
        typer.secho(f"Component '{component}' not found.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)
    typer.echo(f"Component detected: {result.get('script', 'n/a')}")
    typer.echo(f"Status: {result.get('status', 'detected')}")


if __name__ == "__main__":
    app()
