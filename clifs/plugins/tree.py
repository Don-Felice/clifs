# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from pathlib import Path

from clifs.clifs_plugin import ClifsPlugin
from clifs.utils_cli import ANSI_COLORS, size2str, wrap_string

PIPE = "│"
ELBOW = "└──"
TEE = "├──"
PIPE_PREFIX = "│   "
SPACE_PREFIX = "    "


class DirectoryTree(ClifsPlugin):
    """
    Display a tree of the file system including item sizes.
    """

    root_dir: Path
    dirs_only: bool
    hide_sizes: bool

    @staticmethod
    def init_parser(parser: ArgumentParser):
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

    def __init__(self, args):
        super().__init__(args)
        self._tree = []

    def run(self):
        self._add_directory(self.root_dir)
        for entry in self._tree:
            print(entry)

    def _add_directory(  # pylint: disable=too-many-arguments
        self,
        directory,
        index=0,
        entries_count=0,
        prefix="",
        connector="",
        ansiescape_color=ANSI_COLORS["yellow"],
    ) -> int:
        idx_dir = len(
            self._tree
        )  # get index of current directory in tree list to attach size info
        self._tree.append(
            f"{prefix}{connector}"
            + wrap_string(f"{directory.name}", prefix=ansiescape_color)
        )

        if connector == "":  # for root dir
            pass
        elif index != entries_count - 1:
            prefix += PIPE_PREFIX
        else:  # for last sub-dir
            prefix += SPACE_PREFIX

        entries = directory.iterdir()
        try:
            entries = sorted(entries, key=lambda item: (not item.is_file(), str(item)))
        except PermissionError as err:
            print(
                wrap_string(
                    f'Warning: no permission to access "{directory}". '
                    f"Size calculations of parent directories could be off.",
                    prefix=ANSI_COLORS["red"],
                )
            )
            print(wrap_string(f'Error message: "{err}"', prefix=ANSI_COLORS["red"]))
            self._tree[idx_dir] = self._tree[idx_dir] + wrap_string(
                SPACE_PREFIX + "no access", prefix=ANSI_COLORS["red"]
            )
            return 0

        entries_count = len(entries)
        size = 0  # initialize size of sub-directories and files

        for sub_index, entry in enumerate(entries):
            connector = ELBOW if sub_index == entries_count - 1 else TEE
            if entry.is_dir():
                size += self._add_directory(
                    entry, sub_index, entries_count, prefix, connector
                )
            else:
                if self.dirs_only and self.hide_sizes:
                    pass
                else:
                    size += self._add_file(entry, prefix, connector)

        if not self.hide_sizes:
            self._tree[idx_dir] = self._tree[idx_dir] + wrap_string(
                "  " + size2str(size), prefix=ansiescape_color
            )
        return size

    def _add_file(self, file, prefix, connector) -> int:
        try:
            size = file.stat().st_size if not self.hide_sizes else 0
        except FileNotFoundError:
            file_long = Path(
                "\\\\?\\" + str(file)
            )  # handle long paths in windows systems
            size = file_long.stat().st_size if not self.hide_sizes else 0
        if not self.dirs_only:
            if not self.hide_sizes:
                self._tree.append(
                    f"{prefix}{connector} {file.name}" + "  " + size2str(size)
                )
            else:
                self._tree.append(f"{prefix}{connector} {file.name}")
        return size
