from __future__ import annotations

from pathlib import Path

import typer

from .core.models import ProjectConfig
from .core.registry import PROJECT_TYPES, get_framework, get_project_type
from .generator import ProjectGenerator

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


if __name__ == "__main__":
    app()
