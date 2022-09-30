from pathlib import Path

with (Path(__file__).parents[1] / "VERSION").open("r") as version_file:
    __version__ = version_file.read().strip()
