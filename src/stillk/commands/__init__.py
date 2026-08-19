"""CLI command package for Stillk.

This package groups command implementations (tooling, scaffolding adapters)
to keep the top-level `cli.py` small and focused on composition.
"""

from . import tooling

__all__ = ["tooling"]
