from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Framework:
    key: str
    label: str


@dataclass(frozen=True)
class ProjectType:
    key: str
    label: str
    description: str
    template_dir: str
    frameworks: list[Framework] = field(default_factory=list)
    supports_rag_extra: bool = False
    supports_agents_extra: bool = False

    @property
    def default_framework(self) -> Framework | None:
        return self.frameworks[0] if self.frameworks else None


PROJECT_TYPES: dict[str, ProjectType] = {
    "ml": ProjectType(
        key="ml",
        label="Machine Learning",
        description="Machine learning pipeline with training and inference.",
        template_dir="ml",
        frameworks=[
            Framework("scikit-learn", "Scikit-learn"),
            Framework("xgboost", "XGBoost"),
        ],
    ),
    "dl": ProjectType(
        key="dl",
        label="Deep Learning",
        description="Deep learning projects based on PyTorch.",
        template_dir="dl",
        frameworks=[
            Framework("pytorch", "PyTorch"),
        ],
    ),
    "llm": ProjectType(
        key="llm",
        label="LLM",
        description="Large language model projects with prompt and generation flows.",
        template_dir="llm",
        frameworks=[
            Framework("transformers", "Transformers"),
            Framework("langgraph", "LangGraph"),
        ],
        supports_rag_extra=True,
        supports_agents_extra=True,
    ),
    "rag": ProjectType(
        key="rag",
        label="RAG",
        description="Retrieval augmented generation for document-based systems.",
        template_dir="llm",
        frameworks=[
            Framework("langgraph", "LangGraph"),
            Framework("transformers", "Transformers"),
        ],
        supports_rag_extra=True,
    ),
    "agents": ProjectType(
        key="agents",
        label="AI Agents",
        description="Multi-agent orchestration and plan execution.",
        template_dir="llm",
        frameworks=[
            Framework("langgraph", "LangGraph"),
        ],
        supports_agents_extra=True,
    ),
}


def get_project_type(key: str) -> ProjectType:
    try:
        return PROJECT_TYPES[key]
    except KeyError as exc:
        valid = ", ".join(PROJECT_TYPES)
        raise ValueError(f"Project type '{key}' is invalid. Valid options: {valid}") from exc


def get_framework(project_type: ProjectType, key: str) -> Framework:
    for framework in project_type.frameworks:
        if framework.key == key:
            return framework
    valid = ", ".join(framework.key for framework in project_type.frameworks)
    raise ValueError(
        f"Framework '{key}' is invalid for type '{project_type.key}'. Valid options: {valid}"
    )
