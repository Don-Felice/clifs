"""Clifs plugin to show directory trees"""

from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any, List, Optional

from rich.console import Console

from clifs import ClifsPlugin
from clifs.utils_cli import set_style, size2str

PIPE = "│"
ELBOW = "└──"
TEE = "├──"
PIPE_PREFIX = "│   "
SPACE_PREFIX = "    "
SPACE_SIZE = " "


class Entry(ABC):
    """
    Base class for entries in a DirectoryTree
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        path: Path,
        prefix: str = "",
        connector: str = "",
        depth: int = 0,
        plot_size: bool = True,
    ):
        self.path = path
        self.prefix = prefix
        self.connector = connector
        self.depth = depth
        self.plot_size = plot_size

        self.name: str = self.path.name
        self.size: Optional[float] = None

    @abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_size(self) -> Optional[float]:
        """Get the overall size of the entry"""
        raise NotImplementedError


class File(Entry):
    """Representing files in a Directory Tree"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.size: Optional[float] = self.get_size() if self.plot_size else None

    def get_size(self) -> Optional[float]:
        try:
            return self.path.stat().st_size
        except FileNotFoundError:
            file_long = Path(
                "\\\\?\\" + str(self.path)
            )  # handle long paths in windows systems
            return file_long.stat().st_size

    def __str__(self) -> str:
        string = f"{self.prefix}{self.connector} {self.name}"
        if self.plot_size and self.size is not None:
            string += SPACE_SIZE + size2str(self.size)
        return string


class Folder(Entry):
    """
    Representing folders in a DirectoryTree.
    """

    def __init__(
        self,
        dirs_only: bool = False,
        depth_th: Optional[int] = None,
        console: Console = Console(),
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self.dirs_only = dirs_only
        self.depth_th = depth_th
        self.console = console

        self.have_access: bool = True
        self.children: List[Entry] = []

        if (self.depth_th is None or self.depth < self.depth_th) or self.plot_size:
            self.children = self.get_children()

        self.size: Optional[float] = self.get_size() if self.plot_size else None

    def get_children(self) -> List[Entry]:
        children: List[Entry] = []

        items = list(self.path.iterdir())
        try:
            items = sorted(items, key=lambda item: (not item.is_file(), str(item)))
            for num_item, item in enumerate(items, 1):
                child_connector = TEE if num_item < len(items) else ELBOW

                child_prefix = self.prefix
                if self.connector == TEE:  # not last dir
                    child_prefix += PIPE_PREFIX
                elif self.connector == ELBOW:  # last dir
                    child_prefix += SPACE_PREFIX

                if item.is_file() and (not self.dirs_only or self.plot_size):
                    children.append(
                        File(
                            path=item,
                            prefix=child_prefix,
                            connector=child_connector,
                            depth=self.depth + 1,
                            plot_size=self.plot_size,
                        )
                    )
                if item.is_dir():
                    children.append(
                        Folder(
                            path=item,
                            prefix=child_prefix,
                            connector=child_connector,
                            depth=self.depth + 1,
                            depth_th=self.depth_th,
                            dirs_only=self.dirs_only,
                            plot_size=self.plot_size,
                        )
                    )
            return children

        except PermissionError as err:
            self.console.print(
                set_style(
                    f'Error: no permission to access "{self.path}". '
                    "Size calculations of parent directories could be off.",
                    "error",
                )
            )
            self.console.print(set_style(f'Error message: "{err}"', "error"))
            self.have_access = False
            return []

    def get_size(self) -> Optional[float]:
        if not self.have_access:
            return None
        size = 0.0
        for child in self.children:
            size += child.size if child.size is not None else size
        return size

    def __str__(self) -> str:
        string = f"{self.prefix}{self.connector} " if self.depth != 0 else ""
        string += set_style(self.name, "folder")

        if self.plot_size and self.size is not None:
            string += SPACE_SIZE + size2str(self.size)
        elif not self.have_access:
            string += SPACE_SIZE + set_style("no access", "error")

        if (self.depth_th is None or self.depth < self.depth_th) and self.children:
            if self.dirs_only:
                dir_children = [
                    child.__str__()
                    for child in self.children
                    if isinstance(child, Folder)
                ]
                if dir_children:
                    string += "\n" + "\n".join(dir_children)
            else:
                string += "\n" + "\n".join([child.__str__() for child in self.children])
        return string


class DirectoryTree(ClifsPlugin):
    """
    Display a tree of the file system including item sizes.
    """

    root_dir: Path
    dirs_only: bool
    hide_sizes: bool
    depth: int

    @staticmethod
    def init_parser(parser: ArgumentParser) -> None:
        """
        Adding arguments to an argparse parser. Needed for all clifs_plugins.
        """
        parser.add_argument(
            "root_dir",
            type=Path,
            default=".",
            nargs="?",
            help="Root directory to generate tree",
        )
        parser.add_argument(
            "-do",
            "--dirs_only",
            action="store_true",
            default=False,
            help="Get info only on directories",
        )
        parser.add_argument(
            "-hs",
            "--hide_sizes",
            action="store_true",
            default=False,
            help="Hide size information",
        )
        parser.add_argument(
            "-d",
            "--depth",
            type=int,
            default=None,
            help="Max depth to which the tree is plotted",
        )

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.dir: Folder = Folder(
            path=self.root_dir.resolve(),
            plot_size=not self.hide_sizes,
            depth_th=self.depth,
            dirs_only=self.dirs_only,
            console=self.console,
        )

    def __str__(self) -> str:
        return self.dir.__str__()

    def __rich__(self) -> str:
        return self.dir.__str__()

    def run(self) -> None:
        self.console.print(self, highlight=False)
