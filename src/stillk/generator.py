from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, StrictUndefined

from .core.models import ProjectConfig
from .core.registry import get_framework, get_project_type


class ProjectGenerator:
    """Generate a full project from a Stillk configuration."""

    def __init__(self, output_dir: str | Path):
        self.output_dir = Path(output_dir)
        self.env = Environment(autoescape=False, undefined=StrictUndefined)

    def generate(self, config: ProjectConfig) -> Path:
        project_dir = self.output_dir / config.project_slug
        project_dir.mkdir(parents=True, exist_ok=True)

        files = self._build_files(config)
        for relative_path, content in files.items():
            target = project_dir / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

        return project_dir

    def _build_files(self, config: ProjectConfig) -> dict[str, str]:
        context = config.to_context()
        project_type = get_project_type(config.project_type)
        framework = get_framework(project_type, config.framework)
        context["project_type_label"] = project_type.label
        context["framework_label"] = framework.label
        context["use_rag"] = config.include_rag or config.project_type in {"rag", "llm"}
        context["use_agents"] = config.include_agents or config.project_type in {"agents", "llm"}

        files: dict[str, str] = {
            ".gitignore": self._render("""__pycache__/
.pytest_cache/
.venv/
.env
.env.*
*.pyc
*.pyo
*.egg-info/
.coverage
htmlcov/
.DS_Store
""", context),
            ".env.example": self._render("""PROJECT_NAME={{ project_name }}
PROJECT_TYPE={{ project_type }}
FRAMEWORK={{ framework }}
ENVIRONMENT=development
DEBUG=true
""", context),
            "README.md": self._render(
                """# {{ project_name }}

{{ description }}

## Stack
- Python {{ python_version }}
- {{ project_type_label }}
- {{ framework_label }}

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python main.py
```

## Structure

```text
{{ project_name }}/
├── src/
├── tests/
├── configs/
├── data/
├── scripts/
├── Dockerfile
├── pyproject.toml
├── README.md
├── .env.example
└── .gitignore
```
""",
                context,
            ),
            "Dockerfile": self._render(
                """FROM python:{{ python_version }}-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir -e .

CMD [\"python\", \"main.py\"]
""",
                context,
            ),
            "pyproject.toml": self._render(
                """[build-system]
requires = [\"setuptools>=68\", \"wheel\"]
build-backend = \"setuptools.build_meta\"

[project]
name = \"{{ project_slug }}\"
version = \"0.1.0\"
description = \"{{ description }}\"
readme = \"README.md\"
requires-python = \">={{ python_version }}\"
dependencies = [
    \"numpy>=1.26\",
    \"pandas>=2.2\",
    \"pydantic>=2.0\",
    \"typer>=0.12.0\",
    \"jinja2>=3.1.0\",
    \"pyyaml>=6.0.0\",
]

[project.optional-dependencies]
ml = [\"scikit-learn>=1.5.0\", \"xgboost>=2.1.0\"]
dl = [\"torch>=2.4.0\"]
llm = [\"transformers>=4.43.0\", \"langgraph>=0.2.0\"]

[tool.pytest.ini_options]
pythonpath = [\"src\"]
testpaths = [\"tests\"]

[tool.setuptools]
package-dir = {\"\" = \"src\"}

[tool.setuptools.packages.find]
where = [\"src\"]
""",
                context,
            ),
            "main.py": self._render(
                """from __future__ import annotations

from pathlib import Path


def run() -> None:
    print(\"{{ project_name }} initialized successfully.\")
    print(f\"Project type: {{ project_type }}\")
    print(f\"Framework: {{ framework }}\")


if __name__ == \"__main__\":
    run()
""",
                context,
            ),
            "preprocessing.py": self._render(
                """from __future__ import annotations

from pathlib import Path


def prepare_data(data_dir: str | Path) -> Path:
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)
    return data_path


if __name__ == \"__main__\":
    prepare_data(\"data/raw\")
    print(\"Data directory prepared.\")
""",
                context,
            ),
            "configs/settings.yaml": self._render(
                """project:
  name: {{ project_name }}
  type: {{ project_type }}
  framework: {{ framework }}

training:
  epochs: 10
  batch_size: 32
  learning_rate: 0.001
""",
                context,
            ),
            "tests/test_smoke.py": self._render(
                """from __future__ import annotations


def test_project_is_initialised() -> None:
    assert True
""",
                context,
            ),
            "src/__init__.py": self._render("""__all__ = [\"{{ project_slug }}\"]\n""", context),
        }

        if config.project_type in {"ml", "dl"}:
            files.update(
                {
                    "src/data/__init__.py": self._render("""\"\"\"Data utilities.\"\"\"\n""", context),
                    "src/features/__init__.py": self._render("""\"\"\"Feature engineering.\"\"\"\n""", context),
                    "src/models/__init__.py": self._render("""\"\"\"Model definitions.\"\"\"\n""", context),
                    "src/training/train.py": self._render(
                        """from __future__ import annotations


def train_model() -> None:
    print(\"Training pipeline executed for {{ project_name }}.\")


if __name__ == \"__main__\":
    train_model()
""",
                        context,
                    ),
                    "src/inference/predict.py": self._render(
                        """from __future__ import annotations


def predict() -> dict:
    return {\"status\": \"ok\", \"project\": \"{{ project_name }}\"}


if __name__ == \"__main__\":
    print(predict())
""",
                        context,
                    ),
                    "src/api/__init__.py": self._render("""\"\"\"API package.\"\"\"\n""", context),
                    "src/api/main.py": self._render(
                        """from __future__ import annotations


def create_app() -> None:
    print(\"API app created for {{ project_name }}.\")


if __name__ == \"__main__\":
    create_app()
""",
                        context,
                    ),
                    "data/raw/.gitkeep": "",
                    "data/processed/.gitkeep": "",
                    "data/external/.gitkeep": "",
                    "scripts/run_training.sh": self._render("""#!/usr/bin/env bash
python src/training/train.py\n""", context),
                }
            )

        if config.project_type in {"llm", "rag", "agents"}:
            files.update(
                {
                    "src/agents/__init__.py": self._render("""\"\"\"Agent definitions.\"\"\"\n""", context),
                    "src/graph/__init__.py": self._render("""\"\"\"Graph orchestration.\"\"\"\n""", context),
                    "src/nodes/__init__.py": self._render("""\"\"\"Node logic.\"\"\"\n""", context),
                    "src/prompts/__init__.py": self._render("""\"\"\"Prompt templates.\"\"\"\n""", context),
                    "src/tools/__init__.py": self._render("""\"\"\"Tool integrations.\"\"\"\n""", context),
                    "src/retrieval/__init__.py": self._render("""\"\"\"Retrieval components.\"\"\"\n""", context),
                    "src/embeddings/__init__.py": self._render("""\"\"\"Embedding helpers.\"\"\"\n""", context),
                    "src/vectorstore/__init__.py": self._render("""\"\"\"Vector store adapters.\"\"\"\n""", context),
                    "src/evals/__init__.py": self._render("""\"\"\"Evaluation utilities.\"\"\"\n""", context),
                    "src/api/__init__.py": self._render("""\"\"\"API package.\"\"\"\n""", context),
                    "src/api/main.py": self._render(
                        """from __future__ import annotations


def create_api() -> None:
    print(\"LLM API app created for {{ project_name }}.\")


if __name__ == \"__main__\":
    create_api()
""",
                        context,
                    ),
                    "src/graph/graph.py": self._render(
                        """from __future__ import annotations


def build_graph() -> dict:
    return {\"nodes\": [\"loader\", \"retriever\", \"generator\"], \"project\": \"{{ project_name }}\"}
""",
                        context,
                    ),
                    "src/prompts/system_prompt.py": self._render(
                        """SYSTEM_PROMPT = \"You are the assistant for {{ project_name }}.\"\n""",
                        context,
                    ),
                    "src/retrieval/retriever.py": self._render(
                        """from __future__ import annotations


def retrieve(query: str) -> dict:
    return {\"query\": query, \"status\": \"ready\"}
""",
                        context,
                    ),
                    "data/raw/.gitkeep": "",
                    "data/processed/.gitkeep": "",
                    "data/external/.gitkeep": "",
                    "configs/model.yaml": self._render(
                        """model:
  name: {{ framework }}
  provider: {{ project_type }}
  max_tokens: 512
""",
                        context,
                    ),
                }
            )

        return files

    def _render(self, template: str, context: dict[str, Any]) -> str:
        return self.env.from_string(template).render(**context)
