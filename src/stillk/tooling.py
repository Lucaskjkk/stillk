"""Backward compatibility shim for tooling moved to stillk.commands.tooling.

This module keeps `from stillk import tooling` imports working while the
implementation lives in `stillk.commands.tooling` for a cleaner project layout.
"""

from .commands.tooling import *  # noqa: F401,F403

__all__ = [
    name
    for name in dir()
    if not name.startswith("_") and name not in {"name", "__all__"}
]
