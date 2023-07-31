import importlib.metadata
from pathlib import Path

try:
    __version__ = importlib.metadata.version("clifs")
except importlib.metadata.PackageNotFoundError:
    with open(Path(__file__).parent / "VERSION", encoding="UTF-8") as version_file:
        __version__ = version_file.read().strip()
