"""Command line interface for the file system."""

import importlib.metadata
from pathlib import Path

from clifs.clifs_plugin import ClifsPlugin

try:
    __version__ = importlib.metadata.version("clifs")
except importlib.metadata.PackageNotFoundError:
    try:
        import tomllib  # ty: ignore[unresolved-import]
    except ModuleNotFoundError:
        import tomli as tomllib  # ty: ignore[unresolved-import]
    with (Path(__file__).parents[1] / "pyproject.toml").open("rb") as file:
        project_toml = tomllib.load(file)
    __version__ = project_toml["project"]["version"]


__all__ = ["ClifsPlugin"]
