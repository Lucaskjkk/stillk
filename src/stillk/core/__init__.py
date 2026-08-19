"""Core definitions for templates and project metadata."""

from .models import ProjectConfig
from .registry import Framework, ProjectType, PROJECT_TYPES, get_framework, get_project_type

__all__ = [
    "Framework",
    "ProjectConfig",
    "ProjectType",
    "PROJECT_TYPES",
    "get_framework",
    "get_project_type",
]
