# Stillk

Stillk is an open-source scaffolding CLI for machine learning, deep learning, LLM, RAG, and AI agent projects. It follows a create-react-app-inspired workflow so teams can generate a production-ready project skeleton in seconds.

## Why Stillk

- Generate a complete starter project with real folders and working files
- Support ML, DL, LLM, RAG, and AI agents from day one
- Modular registry-based template system for future growth
- Open source and designed for community-driven extension

## Features

- `stillk init <project-name>` to bootstrap a project
- Interactive project selection when flags are omitted
- Built-in templates for ML and LLM flows
- Pre-generated `pyproject.toml`, `README.md`, `Dockerfile`, `.env.example`, tests, and source folders
- Future plugin-ready command: `stillk add mlflow`, `stillk add rag`, `stillk add fastapi`

## Installation

```bash
pip install stillk
```

For local development:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Quick start

```bash
stillk init meu-projeto --project-type ml --framework scikit-learn
stillk init meu-llm --project-type llm --framework transformers
stillk init
```

The interactive mode asks for:

- project type
- framework
- output folder
- project metadata

## Generated project structure

```text
meu-projeto/
├── src/
│   ├── data/
│   ├── features/
│   ├── models/
│   ├── training/
│   ├── inference/
│   ├── api/
│   ├── agents/
│   ├── graph/
│   ├── prompts/
│   ├── retrieval/
│   ├── embeddings/
│   ├── vectorstore/
│   └── evals/
├── data/
│   ├── raw/
│   ├── processed/
│   └── external/
├── configs/
├── notebooks/
├── tests/
├── scripts/
├── Dockerfile
├── pyproject.toml
├── README.md
├── .env.example
├── .gitignore
├── main.py
├── preprocessing.py
└── .github/
```

## Supported types

- Machine Learning
- Deep Learning
- LLM
- RAG
- AI Agents

## Supported frameworks

- Scikit-learn
- PyTorch
- XGBoost
- Transformers
- LangGraph

## Roadmap

- v0.1: core init command and basic templates
- v0.2: `stillk add` plugin system
- v0.3: FastAPI, MLflow, Airflow, and monitoring integrations
- v0.4: community templates and custom template registry

## Publishing to PyPI

To build the package:

```bash
python -m pip install -U build twine
python -m build
```

To publish:

```bash
python -m twine upload dist/*
```

Before publishing, configure your PyPI API token in your environment or use a trusted publishing workflow.

## Contributing

Contributions are welcome. Please open an issue or pull request with tests for new templates or features.

## License

MIT
